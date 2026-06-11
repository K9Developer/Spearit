import Button from "@/components/Button";
import Input from "@/components/Input";
import { Search } from "lucide-react";
import React from "react";

export type SearchFilterOption = {
    value: string;
    label: string;
};

interface Props {
    search: string;
    onSearchChange: (value: string) => void;
    searchPlaceholder: string;
    searchHelperText?: string;
    scopeLabel: string;
    scopeValue: string;
    onScopeChange: (value: string) => void;
    scopeOptions: SearchFilterOption[];
    secondaryLabel?: string;
    secondaryValue?: string;
    onSecondaryChange?: (value: string) => void;
    secondaryOptions?: SearchFilterOption[];
    secondaryHelperText?: string;
    resultText?: string;
    clearLabel?: string;
    onClear: () => void;
}

const selectClassName = "w-full rounded-md outline outline-secondary bg-background/30 px-3 py-2 text-sm text-text-primary [color-scheme:dark]";
const optionClassName = "bg-background text-text-primary";

export default function SearchFilters({
    search,
    onSearchChange,
    searchPlaceholder,
    searchHelperText,
    scopeLabel,
    scopeValue,
    onScopeChange,
    scopeOptions,
    secondaryLabel,
    secondaryValue,
    onSecondaryChange,
    secondaryOptions,
    secondaryHelperText,
    resultText,
    clearLabel = "Clear",
    onClear,
}: Props) {
    const hasSecondaryFilter = Boolean(secondaryOptions?.length && onSecondaryChange);
    const gridClassName = hasSecondaryFilter ? "grid grid-cols-1 xl:grid-cols-[1.5fr_0.75fr_0.75fr_auto] gap-4" : "grid grid-cols-1 xl:grid-cols-[1.7fr_0.85fr_auto] gap-4";

    return (
        <div className="flex flex-col gap-3">
            <div className={gridClassName}>
                <Input title="Search" placeholder={searchPlaceholder} value={search} onChange={onSearchChange} icon={<Search size={16} />} />

                <div className="flex flex-col gap-1">
                    <label className="text-xs uppercase select-none text-text-primary">{scopeLabel}</label>
                    <select value={scopeValue} onChange={(e) => onScopeChange(e.target.value)} className={selectClassName}>
                        {scopeOptions.map((option) => (
                            <option key={option.value} value={option.value} className={optionClassName}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>

                {hasSecondaryFilter && secondaryOptions && onSecondaryChange && secondaryValue !== undefined ? (
                    <div className="flex flex-col gap-1">
                        <label className="text-xs uppercase select-none text-text-primary">{secondaryLabel}</label>
                        <select value={secondaryValue} onChange={(e) => onSecondaryChange(e.target.value)} className={selectClassName}>
                            {secondaryOptions.map((option) => (
                                <option key={option.value} value={option.value} className={optionClassName}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                    </div>
                ) : null}

                <div className="flex items-end gap-3">
                    <Button title={clearLabel} onClick={onClear} className="rounded-xl" />
                </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs text-text-gray">
                    {searchHelperText}
                    {hasSecondaryFilter && secondaryHelperText ? ` ${secondaryHelperText}` : ""}
                </p>
                {resultText && <span className="text-xs uppercase tracking-wide text-text-gray">{resultText}</span>}
            </div>
        </div>
    );
}