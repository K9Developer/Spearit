import React from "react";
import Input from "@/components/Input";

interface Props {
    title: string;
    items: Record<string, string>;
    selected: number[];
    onChange: (next: number[]) => void;
    emptyText?: string;
    disabled?: boolean;
}

export default function IdMultiSelect({ title, items, selected, onChange, emptyText = "None", disabled = false }: Props) {
    const [open, setOpen] = React.useState(false);
    const [query, setQuery] = React.useState("");
    const rootRef = React.useRef<HTMLDivElement | null>(null);

    const options = React.useMemo(() => {
        const parsed = Object.entries(items)
            .map(([idStr, name]) => ({ id: Number(idStr), name }))
            .filter((x) => Number.isFinite(x.id));

        parsed.sort((a, b) => a.id - b.id);
        return parsed;
    }, [items]);

    const selectedSet = React.useMemo(() => new Set(selected), [selected]);

    const filteredOptions = React.useMemo(() => {
        const q = query.trim().toLowerCase();
        if (!q) return options;
        return options.filter((o) => o.name.toLowerCase().includes(q) || String(o.id).includes(q));
    }, [options, query]);

    const toggle = (id: number) => {
        if (disabled) return;
        if (selectedSet.has(id)) onChange(selected.filter((x) => x !== id));
        else onChange([...selected, id]);
    };

    const summary = React.useMemo(() => {
        if (options.length === 0) return emptyText;
        if (selected.length === 0) return "Select…";
        if (selected.length === 1) {
            const only = selected[0];
            const match = options.find((o) => o.id === only);
            return match ? `${match.name} #${match.id}` : `#${only}`;
        }
        return `${selected.length} selected`;
    }, [options, selected, emptyText]);

    React.useEffect(() => {
        if (!open) return;
        const onPointerDown = (e: PointerEvent) => {
            const el = rootRef.current;
            if (!el) return;
            if (e.target instanceof Node && !el.contains(e.target)) setOpen(false);
        };
        window.addEventListener("pointerdown", onPointerDown);
        return () => window.removeEventListener("pointerdown", onPointerDown);
    }, [open]);

    React.useEffect(() => {
        if (!open) setQuery("");
    }, [open]);

    return (
        <div ref={rootRef} className="w-full relative">
            <p className="text-xs uppercase tracking-wide text-text-gray">{title}</p>
            {options.length === 0 ? (
                <p className="mt-2 text-sm text-text-secondary">{emptyText}</p>
            ) : (
                <>
                    <button
                        type="button"
                        onClick={() => {
                            if (!disabled) setOpen((v) => !v);
                        }}
                        disabled={disabled}
                        className={`mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary flex items-center justify-between gap-3 transition ${
                            disabled ? "opacity-70 cursor-not-allowed" : "hover:brightness-90"
                        }`}
                    >
                        <span className="min-w-0 truncate text-left">{summary}</span>
                        <span className="text-xs text-text-gray shrink-0">▾</span>
                    </button>

                    {open && (
                        <div className="absolute z-50 mt-2 w-full rounded-md outline outline-secondary bg-foreground shadow-xl overflow-hidden">
                            <div className="p-2 border-b border-secondary">
                                <Input placeholder="Search…" value={query} onChange={setQuery} disabled={disabled} />
                            </div>
                            <div className="max-h-60 overflow-y-auto p-2">
                                {filteredOptions.length === 0 && <p className="px-3 py-2 text-sm text-text-secondary">No matches</p>}

                                {filteredOptions.map((opt) => {
                                    const isSelected = selectedSet.has(opt.id);
                                    return (
                                        <button
                                            key={opt.id}
                                            type="button"
                                            onClick={() => toggle(opt.id)}
                                            disabled={disabled}
                                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-md transition text-left ${
                                                isSelected ? "bg-background/60" : "hover:bg-background/40"
                                            } ${disabled ? "opacity-70 cursor-not-allowed hover:bg-transparent" : ""}`}
                                        >
                                            <span
                                                className={`h-4 w-4 rounded-sm outline outline-secondary flex items-center justify-center shrink-0 ${
                                                    isSelected ? "bg-highlight/20 outline-highlight" : "bg-background/40"
                                                }`}
                                            >
                                                {isSelected && <span className="text-highlight text-xs">✓</span>}
                                            </span>
                                            <span className="min-w-0 flex-1 truncate text-sm text-text-secondary">{opt.name}</span>
                                            <span className="text-xs text-text-gray shrink-0">#{opt.id}</span>
                                        </button>
                                    );
                                })}
                            </div>
                            <div className="border-t border-secondary px-3 py-2 flex items-center justify-between">
                                <p className="text-xs text-text-gray">{selected.length} selected</p>
                                <button
                                    type="button"
                                    disabled={disabled}
                                    onClick={() => {
                                        if (!disabled) onChange([]);
                                    }}
                                    className={`text-xs text-highlight transition ${disabled ? "opacity-60 cursor-not-allowed" : "hover:brightness-90"}`}
                                >
                                    Clear
                                </button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
