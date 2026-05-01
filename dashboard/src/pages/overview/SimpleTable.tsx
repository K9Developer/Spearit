import React from "react";

export type SimpleTableColumn<Row> = {
    key: string;
    header: string;
    render: (row: Row) => React.ReactNode;
    className?: string;
};

interface Props<Row> {
    columns: SimpleTableColumn<Row>[];
    rows: Row[];
    emptyText?: string;
}

export default function SimpleTable<Row>({ columns, rows, emptyText = "No data" }: Props<Row>) {
    if (rows.length === 0) {
        return <p className="text-sm text-text-gray">{emptyText}</p>;
    }

    return (
        <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-separate border-spacing-0">
                <thead>
                    <tr>
                        {columns.map((col) => (
                            <th key={col.key} className={`text-xs uppercase tracking-wide text-text-gray pb-3 ${col.className ?? ""}`.trim()}>
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, idx) => (
                        <tr key={idx} className="border-t border-secondary/60">
                            {columns.map((col) => (
                                <td key={col.key} className={`py-3 text-sm text-text-primary align-top ${col.className ?? ""}`.trim()}>
                                    {col.render(row)}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
