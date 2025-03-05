import { UserManager, OidcClient } from "oidc-client";
import * as d3 from "d3";

const userManager = new UserManager({
  authority: "https://app.meldrx.com/",
  client_id: "8a9c3cd033de49f2998a74369df478e3",
  response_type: "code",
  redirect_uri: "http://localhost:4434/callback",
});

const normalRangeFemale = {
  bmi: { min: 18.5, max: 24.9 },
  fasting_glucose: { min: 70, max: 99 },
  hdl: { min: 50, max: 80 },
  triglycerides: { min: 0, max: 150 },
  hba1c: { min: 0, max: 5.7 },
  serum_creatinine: { min: 0.59, max: 1.04 },
  alt: { min: 0, max: 30 },
  ast: { min: 8, max: 33 },
};
const normalRangeMale = {
  bmi: { min: 18.5, max: 24.9 },
  fasting_glucose: { min: 70, max: 99 },
  hdl: { min: 40, max: 60 },
  triglycerides: { min: 0, max: 150 },
  hba1c: { min: 0, max: 5.7 },
  serum_creatinine: { min: 0.74, max: 1.35 },
  alt: { min: 0, max: 40 },
  ast: { min: 8, max: 48 },
};
let normalRange = null;

let patientInfo = {}; // Declare a global object

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
        patientInfo.gender = patient.Gender === "1" ? "Male" : "Female";
        if (patient.Gender == 1) {
          normalRange = normalRangeMale;
        } else {
          normalRange = normalRangeFemale;
        }
        patientInfo.hypertension = patient.Hypertension === "1" ? "Yes" : "No";
        patientInfo.smoking = patient.Smoking === "1" ? "Yes" : "No";

        // Insert patient info above charts
        document.getElementById("patient-info").innerHTML = `
           <!--  <h2>Patient Information</h2> -->
           <!-- <p><strong>Patient ID:</strong> ${patient["Patient ID"]}</p>-->
          <p><strong>Age:</strong> ${patient.Age}</p>
          <p><strong>Gender:</strong> ${patientInfo.gender}</p>
          <p><strong>Hypertension:</strong> ${patientInfo.hypertension}</p>
          <p><strong>Smoking Status:</strong> ${patientInfo.smoking}</p>
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
      const categoryUnits = {};

      categories.forEach((category) => {
        // Find the unit for this category (assuming all values have the same unit)
        const unit = data.find((d) => d.Category === category)?.Unit || "";
        categoryUnits[category] = unit; // Store unit for each category
      });

      // Remove loading messages
      document.getElementById("loading-message").style.display = "none";
      createLegend();
      // Create a chart for each category
      categories.forEach((category) => {
        const filteredData = data.filter((d) => d.Category === category);
        if (filteredData.length > 0) {
          createBarChart(filteredData, category, categoryUnits[category]);
          console.log("created a chart");
        }
      });
    })
    .catch((error) => console.error("Error fetching CSV:", error));
}

// Function to create a line chart using D3.js
function createBarChart(data, category, unit) {
  const width = 280, // Reduce width slightly to fit inside the container
    height = 200,
    margin = { top: 30, right: 20, bottom: 50, left: 50 };

  const chartContainer = d3.select("#chart-container");
  const chartDiv = chartContainer
    .append("div")
    .attr("class", "chart")
    .style("width", `${width + margin.left + margin.right}px`) // Ensure consistent width
    .style("overflow", "hidden");

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
    // .attr("fill", "green")
    .attr("fill", (d) => {
      const currange = normalRange[category];
      console.log(currange);
      console.log(category);
      console.log(d.Value);
      return +d.Value < currange.min || +d.Value > currange.max
        ? "orange"
        : "green";
    })
    .attr("opacity", 0.9)
    .on("mouseover", function () {
      d3.select(this).attr("fill", "yellow").attr("opacity", 1); // Change color on hover
    })
    .on("mouseout", function (event, d) {
      // Restore original color after mouse leaves
      const currange = normalRange[category];
      const originalColor =
        +d.Value < currange.min || +d.Value > currange.max ? "orange" : "green";

      d3.select(this).attr("fill", originalColor).attr("opacity", 0.9);
    });

  svg
    .append("line")
    .attr("x1", 0)
    .attr("x2", width)
    .attr("y1", yScale(normalRange[category].max))
    .attr("y2", yScale(normalRange[category].max))
    .attr("stroke", "blue")
    .attr("stroke-dasharray", "5,5");

  svg
    .append("line")
    .attr("x1", 0)
    .attr("x2", width)
    .attr("y1", yScale(normalRange[category].min))
    .attr("y2", yScale(normalRange[category].min))
    .attr("stroke", "blue")
    .attr("stroke-dasharray", "5,5");

  // Append a title for the chart
  chartDiv
    .append("div")
    .style("text-align", "center") // Center align
    .style("margin-top", "10px") // Add some spacing
    .style("font-weight", "bold")
    .style("font-size", "14px") // Adjust font size if needed
    .text(`${category} (${unit})`);
}

// Function to create a legend at the top of all charts
function createLegend() {
  const legendContainer = d3
    .select("#chart-container")
    .insert("div", ":first-child") // Insert legend at the top
    .attr("id", "legend")
    .style("display", "flex")
    .style("justify-content", "center") // Center the legend
    .style("align-items", "center")
    .style("gap", "15px") // Add spacing between legend items
    .style("margin-bottom", "10px"); // Space between legend and charts

  // Normal (Square)
  legendContainer
    .append("span")
    .style("display", "inline-block")
    .style("width", "12px") // Square size
    .style("height", "12px")
    .style("background-color", "green")
    .style("margin-right", "5px");

  legendContainer.append("span").text("Normal");

  // Abnormal (Square)
  legendContainer
    .append("span")
    .style("display", "inline-block")
    .style("width", "12px")
    .style("height", "12px")
    .style("background-color", "orange")
    .style("margin-left", "10px") // Space between legend items
    .style("margin-right", "5px");

  legendContainer.append("span").text("Abnormal");

  // Normal Range (Blue Line)
  legendContainer
    .append("span")
    .style("display", "inline-block")
    .style("width", "20px")
    .style("height", "2px")
    .style("background-color", "blue")
    .style("margin-left", "10px") // Space between legend items
    .style("margin-right", "5px");

  legendContainer.append("span").text("Normal Range");
}

// Call the legend function before drawing charts

// Connect to WebSocket running on Daphne (port 8001)
const socket = new WebSocket("ws://localhost:8001/ws/chat/");

socket.onopen = function () {
  console.log("Connected to WebSocket");
};

// Handle incoming messages from Django
socket.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("AI Response:", data.message);

  // Convert newlines to <br> for HTML rendering
  const formattedMessage = data.message.replace(/\n/g, "<br>");

  // Append message to the chat UI with proper formatting
  document.getElementById("chat-messages").innerHTML += `
    <div class="message bot" style="white-space: pre-line;">${formattedMessage}</div>
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
