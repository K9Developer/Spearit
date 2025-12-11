use crate::{
    constants::{ConsoleApp, GLOBAL_STATE, ScoutWrapperState, term},
    log_warn,
};
use crossterm::{
    event::{
        self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers, MouseEvent, MouseEventKind,
    },
    event::{DisableMouseCapture, EnableMouseCapture},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use ratatui::{
    backend::CrosstermBackend,
    prelude::*,
    style::{Color, Style},
    widgets::*,
};
use std::cmp::min;
use std::io;
use std::time::{Duration, Instant};

fn with_app<F, R>(f: F) -> R
where
    F: FnOnce(&mut ScoutWrapperState) -> R,
{
    let mut guard = GLOBAL_STATE.lock().unwrap();
    f(&mut guard)
}

fn with_app_read<F, R>(f: F) -> R
where
    F: FnOnce(&ScoutWrapperState) -> R,
{
    let guard = GLOBAL_STATE.lock().unwrap();
    f(&guard)
}

#[derive(Clone)]
struct UiSnapshot {
    wrapper: Vec<Line<'static>>,
    loader: Vec<Line<'static>>,
    scroll: [u16; 2],
    auto: [bool; 2],
    current_tab: usize,
    viewport: u16,
    debug: bool,
}

fn snapshot() -> UiSnapshot {
    with_app_read(|app| {
        let filter_debug = |lines: &Vec<Line<'static>>| -> Vec<Line<'static>> {
            if app.terminal.debug {
                lines.clone()
            } else {
                lines
                    .iter()
                    .filter(|line| {
                        if let Some(first_span) = line.spans.first() {
                            first_span.content.as_ref() != "[-]"
                        } else {
                            true
                        }
                    })
                    .cloned()
                    .collect()
            }
        };

        let wrapper = filter_debug(&app.terminal.wrapper);
        let loader = filter_debug(&app.terminal.loader);
        let viewport = app.terminal.viewport as usize;

        let mut scroll = app.terminal.scroll;
        let wrapper_max = wrapper.len().saturating_sub(viewport) as u16;
        let loader_max = loader.len().saturating_sub(viewport) as u16;
        scroll[0] = scroll[0].min(wrapper_max);
        scroll[1] = scroll[1].min(loader_max);

        UiSnapshot {
            wrapper,
            loader,
            scroll,
            auto: app.terminal.auto,
            current_tab: app.terminal.current_tab,
            viewport: app.terminal.viewport,
            debug: app.terminal.debug,
        }
    })
}

fn style_for_prefix(prefix: &str) -> (Style, Style) {
    match prefix {
        "[-]" => (
            Style::default().fg(Color::DarkGray).bold(),
            Style::default().fg(Color::DarkGray),
        ),
        "[*]" => (
            Style::default().fg(Color::Cyan).bold(),
            Style::default().fg(Color::White),
        ),
        "[!]" => (
            Style::default().fg(Color::Yellow).bold(),
            Style::default().fg(Color::LightYellow),
        ),
        "[ERROR]" => (
            Style::default().fg(Color::White).bg(Color::Red).bold(),
            Style::default().fg(Color::White).bg(Color::Red),
        ),
        _ => (
            Style::default().fg(Color::White),
            Style::default().fg(Color::White),
        ),
    }
}

fn build_log_line(mut raw: String) -> Line<'static> {
    raw = raw.replace('\t', " ");

    let (prefix, msg) = if let Some(rest) = raw.strip_prefix("[-] ") {
        ("[-]".to_string(), rest.to_string())
    } else if let Some(rest) = raw.strip_prefix("[*] ") {
        ("[*]".to_string(), rest.to_string())
    } else if let Some(rest) = raw.strip_prefix("[!] ") {
        ("[!]".to_string(), rest.to_string())
    } else if let Some(rest) = raw.strip_prefix("[ERROR] ") {
        ("[ERROR]".to_string(), rest.to_string())
    } else {
        ("".to_string(), raw)
    };

    let (pre_style, msg_style) = style_for_prefix(prefix.as_str());

    if prefix.is_empty() {
        Line::from(Span::styled(msg, msg_style))
    } else {
        Line::from(vec![
            Span::styled(prefix, pre_style),
            Span::raw(" "),
            Span::styled(msg, msg_style),
        ])
    }
}

impl ConsoleApp {
    fn active_lines(&self) -> &Vec<Line<'static>> {
        if self.current_tab == 0 {
            &self.wrapper
        } else {
            &self.loader
        }
    }

    pub fn push_wrapper(&mut self, s: String) {
        let line = build_log_line(s);
        self.wrapper.push(line);

        if self.auto[0] {
            let len = self.wrapper.len();
            let vp = self.viewport as usize;
            let max = len.saturating_sub(vp) as u16;
            self.scroll[0] = max;
        }
    }

    pub fn push_loader(&mut self, s: String) {
        let line = build_log_line(s);
        self.loader.push(line);

        if self.auto[1] {
            let len = self.loader.len();
            let vp = self.viewport as usize;
            let max = len.saturating_sub(vp) as u16;
            self.scroll[1] = max;
        }
    }

    fn clamp_scroll(&mut self) {
        let len = self.active_lines().len();
        let vp = self.viewport as usize;

        let max = len.saturating_sub(vp) as u16;

        if self.scroll[self.current_tab] > max {
            self.scroll[self.current_tab] = max;
        }

        self.auto[self.current_tab] = self.scroll[self.current_tab] == max;
    }

    fn handle_key(&mut self, key: KeyEvent) -> bool {
        if key.kind != KeyEventKind::Press && key.kind != KeyEventKind::Repeat {
            return true;
        }

        if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
            return false;
        }

        match key.code {
            KeyCode::Left => {
                self.current_tab = (self.current_tab + term::NUM_TABS - 1) % term::NUM_TABS;
                self.clamp_scroll();
            }
            KeyCode::Right => {
                self.current_tab = (self.current_tab + 1) % term::NUM_TABS;
                self.clamp_scroll();
            }
            KeyCode::Up => {
                self.auto[self.current_tab] = false;
                self.scroll[self.current_tab] = self.scroll[self.current_tab].saturating_sub(1);
            }

            KeyCode::Down => {
                self.auto[self.current_tab] = false;
                self.scroll[self.current_tab] = self.scroll[self.current_tab].saturating_add(1);
                self.clamp_scroll();
            }

            KeyCode::PageUp => {
                self.auto[self.current_tab] = false;
                self.scroll[self.current_tab] = self.scroll[self.current_tab].saturating_sub(10);
            }

            KeyCode::PageDown => {
                self.auto[self.current_tab] = false;
                self.scroll[self.current_tab] = self.scroll[self.current_tab].saturating_add(10);
                self.clamp_scroll();
            }

            KeyCode::Home => {
                self.auto[self.current_tab] = false;
                self.scroll[self.current_tab] = 0;
            }

            KeyCode::End => {
                let len = self.active_lines().len();
                let vp = self.viewport as usize;
                let max = len.saturating_sub(vp) as u16;

                self.scroll[self.current_tab] = max;
                self.auto[self.current_tab] = true;
            }

            KeyCode::Char('d') => {
                self.debug = !self.debug;
                self.clamp_scroll();
            }

            _ => {}
        }

        true
    }

    fn handle_mouse(&mut self, mouse: MouseEvent) {
        match mouse.kind {
            MouseEventKind::ScrollUp => {
                self.auto[self.current_tab] = false;
                self.scroll[self.current_tab] = self.scroll[self.current_tab].saturating_sub(1);
            }
            MouseEventKind::ScrollDown => {
                self.auto[self.current_tab] = false;
                self.scroll[self.current_tab] = self.scroll[self.current_tab].saturating_add(1);
                self.clamp_scroll();
            }
            MouseEventKind::Down(_) => {
                let (w, h) = crossterm::terminal::size().unwrap();
                let root = Rect {
                    x: 0,
                    y: 0,
                    width: w,
                    height: h,
                };

                let chunks = Layout::default()
                    .direction(Direction::Vertical)
                    .constraints([
                        Constraint::Length(3),
                        Constraint::Min(0),
                        Constraint::Length(3),
                    ])
                    .split(root);

                let tabs_area = chunks[0];

                let content_y = tabs_area.y + 1;
                let inner_x_start = tabs_area.x + 1;
                let inner_x_end = tabs_area.x + tabs_area.width - 1;

                if mouse.row != content_y {
                    return;
                }
                if mouse.column < inner_x_start || mouse.column >= inner_x_end {
                    return;
                }

                let titles = ["  Wrapper  ", "  Loader  "];
                let left_pad = " ";
                let right_pad = " ";
                let divider = "|";

                let mut cursor_x = inner_x_start;

                for (idx, title) in titles.iter().enumerate() {
                    cursor_x = cursor_x.saturating_add(left_pad.len() as u16);

                    let tab_start = cursor_x;

                    cursor_x = cursor_x.saturating_add(title.len() as u16);

                    cursor_x = cursor_x.saturating_add(right_pad.len() as u16);

                    let tab_end = cursor_x; // exclusive

                    if mouse.column >= tab_start && mouse.column < tab_end {
                        if idx < term::NUM_TABS {
                            self.current_tab = idx;
                            self.clamp_scroll();
                        }
                        return;
                    }

                    if idx + 1 < titles.len() {
                        cursor_x = cursor_x.saturating_add(divider.len() as u16);
                    }
                }
            }
            _ => {}
        }
    }
}

fn render_tabs(frame: &mut Frame, area: Rect, snap: &UiSnapshot) {
    let titles = vec![
        Line::from("  Wrapper  ").fg(term::TAB_NORMAL),
        Line::from("  Loader  ").fg(term::TAB_NORMAL),
    ];

    let tabs = Tabs::new(titles)
        .select(snap.current_tab)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(term::BORDER))
                .title(Line::from(" Logs ").bold().fg(term::TITLE)),
        )
        .highlight_style(
            Style::default()
                .fg(term::TAB_SELECTED)
                .bg(term::TAB_BG)
                .bold(),
        );

    frame.render_widget(tabs, area);
}

fn render_logs(frame: &mut Frame, area: Rect, snap: &UiSnapshot) {
    let viewport = snap.viewport as usize;

    let lines = if snap.current_tab == 0 {
        &snap.wrapper
    } else {
        &snap.loader
    };

    let name = if snap.current_tab == 0 {
        "Wrapper"
    } else {
        "Loader"
    };
    let auto = if snap.auto[snap.current_tab] {
        " [AUTO]"
    } else {
        ""
    };

    let log_count = format!(" {} logs ", lines.len());

    let logs = Paragraph::new(lines.clone())
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(term::BORDER))
                .title(
                    Line::from(format!(" {}{} ", name, auto)).style(if auto.is_empty() {
                        Style::default().fg(term::TITLE).bold()
                    } else {
                        Style::default().fg(term::AUTO_COLOR).bold()
                    }),
                )
                .title(
                    Line::from(log_count)
                        .style(Style::default().fg(term::TITLE))
                        .right_aligned(),
                ),
        )
        .scroll((snap.scroll[snap.current_tab], 0));

    frame.render_widget(logs, area);

    if viewport > 0 && lines.len() > viewport {
        let max_scroll = lines.len().saturating_sub(viewport);
        let inside_height = area.height.saturating_sub(2);
        let track = viewport.min(inside_height as usize) as u16;

        let ratio = snap.scroll[snap.current_tab] as f64 / max_scroll.max(1) as f64;

        let thumb = ((viewport as f64 / lines.len() as f64) * track as f64)
            .max(1.0)
            .min(track as f64) as u16;

        let free = track.saturating_sub(thumb);

        let pos = (free as f64 * ratio).round() as u16;
        let max_y = area.y + area.height - 1;

        for i in 0..track {
            let y = area.y + 1 + i;
            if y > max_y {
                break;
            }
            let is_thumb = i >= pos && i < pos.saturating_add(thumb);

            let symbol = if is_thumb { "█" } else { "│" };
            let color = if is_thumb {
                term::SCROLL_THUMB
            } else {
                term::SCROLL_TRACK
            };

            frame.render_widget(
                Paragraph::new(symbol).fg(color),
                Rect {
                    x: area.x + area.width - 1,
                    y,
                    width: 1,
                    height: 1,
                },
            );
        }
    }
}

fn render_help(frame: &mut Frame, area: Rect, debug: bool) {
    let debug_status = if debug { "ON" } else { "OFF" };
    let help = Paragraph::new(vec![Line::from(vec![
        Span::styled("←/→", Style::default().fg(term::HELP_KEY).bold()),
        Span::styled(" Switch  ", Style::default().fg(term::HELP_TEXT)),
        Span::styled("↑/↓", Style::default().fg(term::HELP_KEY).bold()),
        Span::styled(" Scroll  ", Style::default().fg(term::HELP_TEXT)),
        Span::styled("PgUp/PgDn", Style::default().fg(term::HELP_KEY).bold()),
        Span::styled(" Fast Scroll  ", Style::default().fg(term::HELP_TEXT)),
        Span::styled("Home/End", Style::default().fg(term::HELP_KEY).bold()),
        Span::styled(" Top/Bottom  ", Style::default().fg(term::HELP_TEXT)),
        Span::styled("d", Style::default().fg(term::HELP_KEY).bold()),
        Span::styled(
            format!(" Debug [{}]  ", debug_status),
            Style::default().fg(if debug {
                term::AUTO_COLOR
            } else {
                Color::DarkGray
            }),
        ),
        Span::styled("Ctrl+C", Style::default().fg(Color::Red).bold()),
        Span::styled(" Quit", Style::default().fg(term::HELP_TEXT)),
    ])])
    .block(
        Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(term::BORDER))
            .title(Line::from(" Controls ").bold().fg(term::TITLE)),
    )
    .alignment(Alignment::Center);

    frame.render_widget(help, area);
}

fn ui(frame: &mut Frame, snap: &UiSnapshot) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(0),
            Constraint::Length(3),
        ])
        .split(frame.size());

    render_tabs(frame, chunks[0], snap);
    render_logs(frame, chunks[1], snap);
    render_help(frame, chunks[2], snap.debug);
}

pub fn start_terminal() {
    enable_raw_mode().unwrap();
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture).unwrap();

    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend).unwrap();

    let tick = Duration::from_millis(100);
    let mut last = Instant::now();
    let mut first_frame = true;

    loop {
        let snap = snapshot();
        terminal.draw(|f| ui(f, &snap)).unwrap();

        let timeout = tick.checked_sub(last.elapsed()).unwrap_or(Duration::ZERO);

        if event::poll(timeout).unwrap() {
            match event::read().unwrap() {
                Event::Key(k) => {
                    if !with_app(|app| app.terminal.handle_key(k)) {
                        break;
                    }
                }
                Event::Mouse(m) => {
                    with_app(|app| app.terminal.handle_mouse(m));
                }
                _ => {}
            }
        }

        if last.elapsed() >= tick {
            last = Instant::now();
            let view_h = terminal.size().unwrap().height.saturating_sub(3 + 3 + 2); // tabs(3) + help(3) + log borders(2)

            with_app(|app| {
                app.terminal.viewport = view_h;

                if first_frame {
                    app.terminal.auto = [true, true];
                    app.terminal.scroll = [u16::MAX, u16::MAX];
                    app.terminal.clamp_scroll();
                } else {
                    app.terminal.clamp_scroll();
                }
            });

            first_frame = false;
        }
    }

    disable_raw_mode().unwrap();
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )
    .unwrap();
    terminal.show_cursor().unwrap();

    with_app(|app| {
        app.is_running = false;
    });
}
