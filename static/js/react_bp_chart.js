console.log("React BP Chart loaded successfully!");
const { useEffect, useState } = React;
const { render } = ReactDOM;

const BPChart = ({ patientId }) => {
  console.log("BPChart component is rendering...");
  const [bpData, setBpData] = useState([]);

  useEffect(() => {
    console.log("Fetch data from patient: ", patientId);
    console.log(window.location);
    fetch(`/bpapp/api/${patientId}/`) // Django API endpoint
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
  console.log("return canvas");
  return React.createElement("canvas", { id: "bpChart" });
};

// Mount the React component to a Django template element
const rootElement = document.getElementById("react-bp-chart");
if (rootElement) {
  console.log("Mounting React component...");
  ReactDOM.render(
    React.createElement(BPChart, {
      patientId: rootElement.dataset.patientId,
    }),
    rootElement
  );
} else {
  console.error("Error: Could not find `react-bp-chart` div in HTML!");
}
