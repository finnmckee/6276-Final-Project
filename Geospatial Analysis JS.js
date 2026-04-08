function _1(md){return(
md`# NC Counties

Chloropleth of NC Counties and the Magnitude of SNAP Threshold - Average Cost per Meal Normalized`
)}

function _map(normalizeSnapCost,d3,map_width,map_height,counties,geoGenerator,M,tippy)
{
  normalizeSnapCost;  // ensures GAP is computed

  const svg = d3.create("svg")
    .attr("width", map_width)
    .attr("height", map_height);

  const county_group = svg.append("g")
    .selectAll("path")
    .data(counties.features)
    .enter()
    .append("path")
      .attr("d", geoGenerator)
      .style("stroke", "black")
      .style("stroke-width", "1px")
      .style("fill", d => {
        const g = d.properties.GAP;
        if (g == null || isNaN(g)) return "#eee";
        const t = Math.pow(g / M, 0.8);
        return d3.interpolateBlues(t);
      })
      .attr("title", d => {
        const snap = d.properties.SNAP;
        const cost = d.properties.COST;
        const gap  = d.properties.GAP;

        const snapText = (snap == null || isNaN(snap))
          ? "N/A"
          : `${(snap * 100).toFixed(0)}% of poverty line`;

        const costText = (cost == null || isNaN(cost))
          ? "N/A"
          : `$${cost.toFixed(2)} per meal`;

        const gapText = (gap == null || isNaN(gap))
          ? "N/A"
          : gap.toFixed(2);

        return `${d.properties.NAMELSAD}
SNAP threshold: ${snapText}
Avg cost per meal: ${costText}
Normalized gap: ${gapText}`;
      })
      // Hover highlight
      .on("mouseover", function () {
        d3.select(this)
          .raise()
          .style("stroke-width", "2px");
      })
      .on("mouseout", function () {
        d3.select(this)
          .style("stroke-width", "1px");
      });

  county_group.nodes().forEach(tippy);

  return svg.node();
}


function _food_raw(FileAttachment){return(
FileAttachment("county_data.csv").csv()
)}

function _food_nc_2022(food_raw){return(
food_raw.filter(d => d.State === "NC" && d.Year === "2022")
)}

function _foodByCounty(d3,food_nc_2022){return(
d3.group(
  food_nc_2022,
  d => d["County, State"].replace(", North Carolina", "") // "Wake County, North Carolina" → "Wake County"
)
)}

function _prepareFoodData(counties,foodByCounty)
{
  counties.features.forEach(f => {
    const name = f.properties.NAMELSAD;
    const rows = foodByCounty.get(name);

    if (rows && rows.length) {
      const row = rows[0];

      // Food insecurity stuff (optional)
      const rateStr  = row["Overall Food Insecurity Rate"] || "";
      const rate     = +rateStr.replace("%", "");
      const countStr = row[" # of Food Insecure Persons Overall "] || "";
      const count    = +countStr.replace(/,/g, "");
      f.properties.FI_RATE  = rate;
      f.properties.FI_COUNT = count;

      // SNAP Threshold (e.g. "200%")
      let snapStr = (row["SNAP Threshold"] || "").trim();
      let snapVal = NaN;
      if (snapStr.endsWith("%")) {
        snapVal = parseFloat(snapStr.replace("%", "")) / 100;  // "200%" → 2.0
      } else {
        snapVal = parseFloat(snapStr); // just in case some are like "1.3"
      }
      f.properties.SNAP = snapVal;  // multiple of poverty line

      // Average Cost Per Meal (e.g. "$4.08 ")
      let costStr = (row["Average Cost Per Meal"] || "").trim();
      costStr = costStr.replace("$", "");
      const costVal = parseFloat(costStr);
      f.properties.COST = costVal;

    } else {
      f.properties.FI_RATE  = null;
      f.properties.FI_COUNT = null;
      f.properties.SNAP     = null;
      f.properties.COST     = null;
    }
  });

  return counties;
}


function _normalizeSnapCost(prepareFoodData,counties,d3)
{
  // Make sure county properties exist
  prepareFoodData;

  const snapVals = [];
  const costVals = [];

  counties.features.forEach(f => {
    const s = f.properties.SNAP;
    const c = f.properties.COST;
    if (Number.isFinite(s)) snapVals.push(s);
    if (Number.isFinite(c)) costVals.push(c);
  });

  const snapMin = d3.min(snapVals);
  const snapMax = d3.max(snapVals);
  const costMin = d3.min(costVals);
  const costMax = d3.max(costVals);

  counties.features.forEach(f => {
    const s = f.properties.SNAP;
    const c = f.properties.COST;

    let sn = null;
    let cn = null;

    // SNAP normalized: fallback to 0.5 if constant across counties
    if (Number.isFinite(s)) {
      if (snapMax > snapMin) {
        sn = (s - snapMin) / (snapMax - snapMin);
      } else {
        // all SNAP are the same (your case in NC) – treat as middle value
        sn = 0.5;
      }
    }

    // Cost normalized as usual
    if (Number.isFinite(c) && costMax > costMin) {
      cn = (c - costMin) / (costMax - costMin);
    }

    f.properties.SNAP_N = sn;
    f.properties.COST_N = cn;

    if (Number.isFinite(sn) && Number.isFinite(cn)) {
      f.properties.GAP = Math.abs(sn - cn);
    } else {
      f.properties.GAP = null;
    }
  });

  return { snapMin, snapMax, costMin, costMax };
}


function _M(normalizeSnapCost,d3,counties)
{
  normalizeSnapCost;
  return d3.max(counties.features, c => c.properties.GAP);
}


function _colorScale(normalizeSnapCost,M,d3)
{
  normalizeSnapCost;  // make sure GAP & M exist

  const maxGap = M || 1;

  // Returns the fill color for a GAP value
  return function(g) {
    if (g == null || isNaN(g)) return "#eee";
    const t = Math.pow(g / maxGap, 0.8); // same non-linear stretch you had
    return d3.interpolateBlues(t);
  };
}


function _legend(normalizeSnapCost,d3,M)
{
  normalizeSnapCost;  // ensure GAP/M computed

  const width = 260;
  const height = 60;
  const barHeight = 12;

  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

  const defs = svg.append("defs");
  const gradientId = "gap-legend-gradient";

  const gradient = defs.append("linearGradient")
    .attr("id", gradientId)
    .attr("x1", "0%").attr("y1", "0%")
    .attr("x2", "100%").attr("y2", "0%");

  const maxGap = M || 1;
  const n = 50;

  for (let i = 0; i < n; ++i) {
    const t = i / (n - 1);
    const g = t * maxGap;
    gradient.append("stop")
      .attr("offset", `${t * 100}%`)
      .attr("stop-color", d3.interpolateBlues(Math.pow(g / maxGap, 0.8)));
  }

  const marginLeft = 40;
  const marginTop = 20;
  const barWidth = width - marginLeft - 20;

  svg.append("rect")
    .attr("x", marginLeft)
    .attr("y", marginTop)
    .attr("width", barWidth)
    .attr("height", barHeight)
    .attr("fill", `url(#${gradientId})`)
    .attr("stroke", "#ccc");

  const xScale = d3.scaleLinear()
    .domain([0, maxGap])
    .range([marginLeft, marginLeft + barWidth]);

  const axis = d3.axisBottom(xScale)
    .ticks(5)
    .tickFormat(d3.format(".2f"));

  svg.append("g")
    .attr("transform", `translate(0, ${marginTop + barHeight})`)
    .call(axis);

  svg.append("text")
    .attr("x", marginLeft)
    .attr("y", marginTop - 6)
    .attr("font-size", 12)
    .attr("font-weight", "bold")
    .text("Normalized GAP (|SNAP – Cost|)");

  return svg.node();
}


function _mapWithLegend(html,map,legend)
{
  const container = html`<div style="display: inline-block; text-align: left;"></div>`;

  // Title
  const title = html`<h3 style="margin: 0 0 4px 0;">
    Normalized GAP Between SNAP Threshold and Meal Cost by County (NC)
  </h3>`;

  const subtitle = html`<div style="font-size: 0.85rem; color: #555; margin-bottom: 10px;">
    Darker counties represent a larger mismatch between SNAP eligibility and the average cost per meal.
  </div>`;

  container.append(title);
  container.append(subtitle);

  // Map + legend
  container.append(map);
  container.append(legend);

  return container;
}


function _geoGenerator(d3,projection){return(
d3.geoPath().projection(projection)
)}

function _projection(d3,map_width,map_height,counties){return(
d3
  .geoIdentity()
  .reflectY(true)
  .fitSize([map_width, map_height], counties)
)}

function _counties(topojson,nc){return(
topojson.feature(nc, nc.objects.nc_counties)
)}

function _nc(FileAttachment){return(
FileAttachment('county_pops.json').json()
)}

function _map_height(map_width){return(
0.6 * map_width
)}

function _map_width(width){return(
0.9 * width
)}

function _tippy(require){return(
require("https://unpkg.com/tippy.js@2.5.4/dist/tippy.all.min.js")
)}

function _topojson(require){return(
require("topojson-client@3")
)}

function _d3(require){return(
require('d3@6')
)}

export default function define(runtime, observer) {
  const main = runtime.module();
  function toString() { return this.url; }
  const fileAttachments = new Map([
    ["county_data.csv", {url: new URL("./files/e40e5715297959b1f16e06a246d4caa7991c89d4c827eece42838aa706a0fff10b9669bc06e6d08c7f606ebfac8e59222336f19fb2a12a98dcde6a92035aebb8.csv", import.meta.url), mimeType: "text/csv", toString}],
    ["county_pops.json", {url: new URL("./files/c383a6950a4ed9916459f8d57949a61ae6cea3fd5c91f3b65a2108f8f0352ac6f815b8be327aa7bc35aa781b3f2210a5e5c3c1a639ad60d4ce8914c29ef65d70.json", import.meta.url), mimeType: "application/json", toString}]
  ]);
  main.builtin("FileAttachment", runtime.fileAttachments(name => fileAttachments.get(name)));
  main.variable(observer()).define(["md"], _1);
  main.variable(observer("map")).define("map", ["normalizeSnapCost","d3","map_width","map_height","counties","geoGenerator","M","tippy"], _map);
  main.variable(observer("food_raw")).define("food_raw", ["FileAttachment"], _food_raw);
  main.variable(observer("food_nc_2022")).define("food_nc_2022", ["food_raw"], _food_nc_2022);
  main.variable(observer("foodByCounty")).define("foodByCounty", ["d3","food_nc_2022"], _foodByCounty);
  main.variable(observer("prepareFoodData")).define("prepareFoodData", ["counties","foodByCounty"], _prepareFoodData);
  main.variable(observer("normalizeSnapCost")).define("normalizeSnapCost", ["prepareFoodData","counties","d3"], _normalizeSnapCost);
  main.variable(observer("M")).define("M", ["normalizeSnapCost","d3","counties"], _M);
  main.variable(observer("colorScale")).define("colorScale", ["normalizeSnapCost","M","d3"], _colorScale);
  main.variable(observer("legend")).define("legend", ["normalizeSnapCost","d3","M"], _legend);
  main.variable(observer("mapWithLegend")).define("mapWithLegend", ["html","map","legend"], _mapWithLegend);
  main.variable(observer("geoGenerator")).define("geoGenerator", ["d3","projection"], _geoGenerator);
  main.variable(observer("projection")).define("projection", ["d3","map_width","map_height","counties"], _projection);
  main.variable(observer("counties")).define("counties", ["topojson","nc"], _counties);
  main.variable(observer("nc")).define("nc", ["FileAttachment"], _nc);
  main.variable(observer("map_height")).define("map_height", ["map_width"], _map_height);
  main.variable(observer("map_width")).define("map_width", ["width"], _map_width);
  main.variable(observer("tippy")).define("tippy", ["require"], _tippy);
  main.variable(observer("topojson")).define("topojson", ["require"], _topojson);
  main.variable(observer("d3")).define("d3", ["require"], _d3);
  return main;
}
