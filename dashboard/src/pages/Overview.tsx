import APIManager from "@/utils/api_manager";
import React, { useEffect } from "react";

const Overview = () => {
    useEffect(() => {
        APIManager.getOverviewData().then((res) => {
            if (res.success) {
                console.log(res.data);
            } else {
                console.error("Failed to fetch overview data:", res.message);
            }
        });
    }, []);

    return <div>Overview</div>;
};

export default Overview;
