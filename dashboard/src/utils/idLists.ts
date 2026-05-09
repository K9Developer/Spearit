export const parseIdList = (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) return [];

    const parts = trimmed.split(/[\s,]+/g).filter(Boolean);
    const ids = parts
        .map((p) => Number(p))
        .filter((n) => Number.isFinite(n) && n >= 0)
        .map((n) => Math.trunc(n));

    return Array.from(new Set(ids)).sort((a, b) => a - b);
};

export const sameIds = (a: number[] | null | undefined, b: number[] | null | undefined) => {
    const aa = (a ?? []).slice().sort((x, y) => x - y);
    const bb = (b ?? []).slice().sort((x, y) => x - y);
    if (aa.length !== bb.length) return false;
    for (let i = 0; i < aa.length; i++) {
        if (aa[i] !== bb[i]) return false;
    }
    return true;
};
