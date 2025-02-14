import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom";
import Chart from "chart.js/auto";

console.log("React BP Chart loaded successfully!");

const BPChart = ({ patientId }) => {
  const [bpData, setBpData] = useState([]);

  useEffect(() => {
    fetch(`/bp/api/${patientId}/`) // Django API endpoint
      .then((response) => response.json())
      .then((data) => setBpData(data.bp_readings));
  }, [patientId]);

  useEffect(() => {
    if (bpData.length === 0) return;

    const labels = bpData.map((r) => r.date);
    const systolic = bpData.map((r) => r.systolic);
    const diastolic = bpData.map((r) => r.diastolic);

    const ctx = document.getElementById("bpChart").getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Systolic",
            data: systolic,
            borderColor: "red",
            fill: false,
          },
          {
            label: "Diastolic",
            data: diastolic,
            borderColor: "blue",
            fill: false,
          },
        ],
      },
    });
  }, [bpData]);

  return <canvas id="bpChart"></canvas>;
};

// Mount the React component to a Django template element
const rootElement = document.getElementById("react-bp-chart");
if (rootElement) {
  ReactDOM.render(
    <BPChart patientId={rootElement.dataset.patientId} />,
    rootElement
  );
}
