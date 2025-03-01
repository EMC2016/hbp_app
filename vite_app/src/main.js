import { UserManager, OidcClient } from "oidc-client";
import * as d3 from "d3";

const userManager = new UserManager({
  authority: "https://app.meldrx.com/",
  client_id: "8a9c3cd033de49f2998a74369df478e3",
  response_type: "code",
  redirect_uri: "http://localhost:4434/callback",
});

if (window.location.pathname === "/launch") {
  console.log("launch", window.location);
  const extraQueryParams = {};
  const params = window.location.search
    .split("?")[1]
    .split("&")
    .map((x) => x.split("="));

  for (const kv of params) {
    extraQueryParams[kv[0] === "iss" ? "aud" : kv[0]] = kv[1];
  }
  console.log(extraQueryParams);

  userManager.signinRedirect({
    scope: "openid profile patient/*.* launch",
    extraQueryParams,
  });
} else if (window.location.pathname === "/callback") {
  console.log("callback", window.location);
  var oidc = new OidcClient({
    authority: "https://app.meldrx.com/",
    client_id: "8a9c3cd033de49f2998a74369df478e3",
    response_type: "code",
    redirect_uri: "http://localhost:4434/callback",
  });
  oidc.processSigninResponse(window.location.href).then((result) => {
    console.log("Patient ID:", result.patient);
    const patientId = result.patient;

    // Construct CSV file path
    //     const csvFilePath = `/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/hyertension_project/django_project/extracted_data_${patientId}.csv
    // `;
    //     console.log("Fetching CSV from:", csvFilePath);
    const csvFilePath = new URL(
      `./assets/extracted_data_${patientId}.csv`,
      import.meta.url
    ).href;

    console.log("Fetching CSV from:", csvFilePath);

    // Fetch and visualize the CSV
    fetchAndVisualize(csvFilePath);
  });
  // userManager.signinCallback().then((result) => console.log(result));
}
// Function to fetch CSV and visualize it using D3.js
function fetchAndVisualize(csvPath) {
  d3.csv(csvPath)
    .then((data) => {
      console.log("CSV Data:", data);

      // Convert timestamp to Date objects and values to numbers
      data.forEach((d) => {
        d.Timestamp = new Date(d.Timestamp);
        d.Value = parseFloat(d.Value); // Ensure Value is a number
      });

      // Remove invalid data points
      data = data.filter((d) => !isNaN(d.Value) && !isNaN(d.Timestamp));

      // Sort data chronologically
      data.sort((a, b) => a.Timestamp - b.Timestamp);

      // Group data by Category
      const categories = [...new Set(data.map((d) => d.Category))];

      // Remove loading messages
      document.getElementById("loading-message").style.display = "none";

      // Create a chart for each category
      categories.forEach((category) => {
        const filteredData = data.filter((d) => d.Category === category);
        if (filteredData.length > 0) {
          createBarChart(filteredData, category);
          console.log("created a chart");
        }
      });
    })
    .catch((error) => console.error("Error fetching CSV:", error));
}

// Function to create a line chart using D3.js
function createBarChart(data, category) {
  const width = 600,
    height = 350,
    margin = { top: 50, right: 40, bottom: 70, left: 70 };

  // Define a color scale
  const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

  // Select the chart container and create a new div for each chart
  const chartContainer = d3.select("#chart-container");
  const chartDiv = chartContainer
    .append("div")
    .attr("class", "chart")
    .style("width", `${width + margin.left + margin.right}px`)
    .style("margin", "10px auto");

  // Append a title for the chart
  chartDiv
    .append("h3")
    .style("font-weight", "bold")
    .style("font-size", "20px") // Bigger title
    .text(category);

  // Append an SVG inside the new chart div
  const svg = chartDiv
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // X Scale (Band Scale for bars)
  const xScale = d3
    .scaleBand()
    .domain(data.map((d) => d.Timestamp))
    .range([0, width])
    .padding(0.05); // Smaller padding for tighter bars

  // Y Scale
  const yScale = d3
    .scaleLinear()
    .domain([0, d3.max(data, (d) => +d.Value) * 1.1])
    .range([height, 0]);

  // X Axis
  svg
    .append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%Y-%m")).ticks(5))
    .selectAll("text")
    .attr("transform", "rotate(-45)")
    .style("text-anchor", "end")
    .style("font-size", "16px"); // Increase font size

  // Y Axis
  svg
    .append("g")
    .call(d3.axisLeft(yScale).ticks(6)) // More readable ticks
    .style("font-size", "16px"); // Increase font size

  // Bars with reduced spacing and larger width
  svg
    .selectAll("rect")
    .data(data)
    .enter()
    .append("rect")
    .attr("x", (d) => xScale(d.Timestamp))
    .attr("y", (d) => yScale(+d.Value))
    .attr("width", xScale.bandwidth() * 0.9) // Slightly wider bars
    .attr("height", (d) => height - yScale(+d.Value))
    .attr("fill", "green")
    .attr("opacity", 0.9)
    .on("mouseover", function () {
      d3.select(this).attr("fill", "orange");
    })
    .on("mouseout", function () {
      d3.select(this).attr("fill", "green");
    });

  // Add Labels to Bars
  svg
    .selectAll(".bar-label")
    .data(data)
    .enter()
    .append("text")
    .attr("class", "bar-label")
    .attr("x", (d) => xScale(d.Timestamp) + xScale.bandwidth() / 2)
    .attr("y", (d) => yScale(+d.Value) - 5)
    .attr("text-anchor", "middle")
    .style("font-size", "14px") // Bigger labels
    .style("font-weight", "bold")
    .text((d) => d.Value.toFixed(2)); // Show values with 2 decimal places
}

// Connect to WebSocket running on Daphne (port 8001)
const socket = new WebSocket("ws://localhost:8001/ws/chat/");

socket.onopen = function () {
  console.log("Connected to WebSocket");
};

// Handle incoming messages from Django
socket.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("AI Response:", data.message);

  // Append message to the chat UI
  document.getElementById("chat-messages").innerHTML += `
    <div class="message bot">${data.message}</div>
  `;
};

// Send user messages to the WebSocket
function sendMessage() {
  const userInput = document.getElementById("user-input").value;
  document.getElementById("chat-messages").innerHTML += `
    <div class="message user">${userInput}</div>
  `;

  socket.send(JSON.stringify({ message: userInput }));
  document.getElementById("user-input").value = ""; // Clear input field
}

function handleKeyPress(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
}
