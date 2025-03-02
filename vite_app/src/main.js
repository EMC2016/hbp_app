import { UserManager, OidcClient } from "oidc-client";
import * as d3 from "d3";

const userManager = new UserManager({
  authority: "https://app.meldrx.com/",
  client_id: "8a9c3cd033de49f2998a74369df478e3",
  response_type: "code",
  redirect_uri: "http://localhost:4434/callback",
});

// let patientId = null;

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
    const patientId = result.patient;
    console.log("Patient ID:", patientId);

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
  const patientInfoPath = csvPath.replace("extracted_data_", "patient_info_"); // Get patient info CSV path
  const reportPath = csvPath
    .replace("extracted_data_", "report_")
    .replace(".csv", ".json");
  console.log("Fetching JSON from:", reportPath);
  d3.csv(patientInfoPath)
    .then((patientData) => {
      if (patientData.length > 0) {
        const patient = patientData[0]; // Assuming only one row exists

        // Convert values if needed
        const genderText = patient.Gender === "1" ? "Male" : "Female";
        const hypertensionText = patient.Hypertension === "1" ? "Yes" : "No";
        const smokingText = patient.Smoking === "1" ? "Yes" : "No";

        // Insert patient info above charts
        document.getElementById("patient-info").innerHTML = `
          <h2>Patient Information</h2>
          <p><strong>Patient ID:</strong> ${patient["Patient ID"]}</p>
          <p><strong>Age:</strong> ${patient.Age}</p>
          <p><strong>Gender:</strong> ${genderText}</p>
          <p><strong>Hypertension:</strong> ${hypertensionText}</p>
          <p><strong>Smoking Status:</strong> ${smokingText}</p>
          <hr>
        `;
      }
      return fetch(reportPath);
      // Now fetch and visualize charts
      // return d3.csv(csvPath);
    })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json(); // Correctly parse JSON
    })
    .then((reportData) => {
      console.log("Fetched CVD Risk Report:", reportData);

      // Call function to update the UI with the risk report
      updateCvdRiskReport(reportData);

      // Fetch and visualize the CSV data for charting
      return d3.csv(csvPath);
    })
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
  const width = 280, // Reduce width slightly to fit inside the container
    height = 200,
    margin = { top: 30, right: 20, bottom: 50, left: 50 };

  const chartContainer = d3.select("#chart-container");
  const chartDiv = chartContainer
    .append("div")
    .attr("class", "chart")
    .style("width", `${width + margin.left + margin.right}px`) // Ensure consistent width
    .style("overflow", "hidden");

  // Append a title for the chart
  chartDiv.append("h3").style("font-weight", "bold").text(category);

  const svg = chartDiv
    .append("svg")
    .attr("width", "100%") // Allow full width but respect container limits
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // X Scale
  const xScale = d3
    .scaleBand()
    .domain(data.map((d) => d.Timestamp))
    .range([0, width])
    .padding(0.3);

  // Y Scale
  const yScale = d3
    .scaleLinear()
    .domain([0, d3.max(data, (d) => +d.Value) * 1.1])
    .range([height, 0]);

  // X Axis
  svg
    .append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%Y-%m")).ticks(3))
    .selectAll("text")
    .attr("transform", "rotate(-45)")
    .style("text-anchor", "end")
    .style("font-size", "12px");

  // Y Axis
  svg.append("g").call(d3.axisLeft(yScale).ticks(4)).style("font-size", "12px");

  // Bars
  svg
    .selectAll("rect")
    .data(data)
    .enter()
    .append("rect")
    .attr("x", (d) => xScale(d.Timestamp))
    .attr("y", (d) => yScale(+d.Value))
    .attr("width", xScale.bandwidth() * 0.7) // Reduce width to fit correctly
    .attr("height", (d) => height - yScale(+d.Value))
    .attr("fill", "green")
    .attr("opacity", 0.9)
    .on("mouseover", function () {
      d3.select(this).attr("fill", "organge").attr("opacity", 1);
    })
    .on("mouseout", function () {
      d3.select(this).attr("fill", "green").attr("opacity", 0.9);
    });
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

window.sendMessage = function () {
  const userInput = document.getElementById("user-input").value;
  document.getElementById("chat-messages").innerHTML += `
    <div class="message user">${userInput}</div>
  `;

  socket.send(JSON.stringify({ message: userInput }));
  document.getElementById("user-input").value = ""; // Clear input field
};

window.handleKeyPress = function (event) {
  if (event.key === "Enter") {
    sendMessage();
  }
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

function updateCvdRiskReport(reportData) {
  console.log("Received Report Data:", JSON.stringify(reportData, null, 2));

  const reportContainer = document.getElementById("cvd-report");

  if (!reportContainer) {
    console.error("CVD report container not found in the HTML.");
    return;
  }

  // reportContainer.innerHTML = "<h2>Cardiovascular Risk Report</h2>";

  // Ensure reportData is valid
  if (!reportData || typeof reportData !== "object") {
    reportContainer.innerHTML += `<p style="color: red;">Error: Invalid or missing report data.</p>`;
    console.error("Received invalid reportData:", reportData);
    return;
  }

  // Handle API error responses
  if (reportData.error) {
    reportContainer.innerHTML += `<p style="color: red;">${reportData.error}</p>`;
    return;
  }

  // Overall Risk Estimate
  const overallRisk = reportData["Overall Risk Estimate"] || "Unknown";
  reportContainer.innerHTML += `<p><strong>Overall Risk Estimate:</strong> ${overallRisk}</p>`;

  // Risk Factor Assessment
  let riskFactorsHTML = "<h3>Risk Factors:</h3><ul>";
  if (
    reportData["Risk Factor Assessment"] &&
    typeof reportData["Risk Factor Assessment"] === "object"
  ) {
    riskFactorsHTML += generateNestedList(reportData["Risk Factor Assessment"]);
  } else {
    riskFactorsHTML += "<li>No risk factor data available.</li>";
  }
  riskFactorsHTML += "</ul>";
  reportContainer.innerHTML += riskFactorsHTML;

  // Recommendations
  let recommendationsHTML = "<h3>Recommendations:</h3><ul>";
  if (
    reportData.Recommendations &&
    typeof reportData.Recommendations === "object"
  ) {
    recommendationsHTML += generateNestedList(reportData.Recommendations);
  } else {
    recommendationsHTML += "<li>No recommendations available.</li>";
  }
  recommendationsHTML += "</ul>";
  reportContainer.innerHTML += recommendationsHTML;
}

// Helper function to handle nested objects
function generateNestedList(obj) {
  let html = "";
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === "object" && value !== null) {
      html += `<li><strong>${key}:</strong><ul>${generateNestedList(
        value
      )}</ul></li>`;
    } else {
      html += `<li><strong>${key}:</strong> ${value}</li>`;
    }
  }
  return html;
}
