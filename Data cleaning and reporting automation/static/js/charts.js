/**
 * Plotly Interactive Chart Renderers for AutoCleanPro Dashboard
 */

const Charts = {
    renderQualityGauge(elementId, score, title = "Data Quality Score") {
        let gaugeColor = "#ef4444";
        if (score >= 90) gaugeColor = "#10b981";
        else if (score >= 75) gaugeColor = "#3b82f6";
        else if (score >= 60) gaugeColor = "#f59e0b";

        const data = [{
            type: "indicator",
            mode: "gauge+number",
            value: score,
            title: { text: title, font: { size: 16, color: "#0f172a" } },
            number: { suffix: "%", font: { size: 36, color: "#0f172a", family: "Inter" } },
            gauge: {
                axis: { range: [0, 100], tickwidth: 1, tickcolor: "#cbd5e1" },
                bar: { color: gaugeColor },
                bgcolor: "white",
                borderwidth: 2,
                bordercolor: "#e2e8f0",
                steps: [
                    { range: [0, 40], color: "#fee2e2" },
                    { range: [40, 75], color: "#fef3c7" },
                    { range: [75, 90], color: "#dbeafe" },
                    { range: [90, 100], color: "#d1fae5" }
                ]
            }
        }];

        const layout = {
            margin: { t: 40, b: 20, l: 30, r: 30 },
            paper_bgcolor: "transparent",
            font: { family: "Inter" },
            height: 250
        };

        Plotly.newPlot(elementId, data, layout, { responsive: true, displayModeBar: false });
    },

    renderMissingChart(elementId, missingData) {
        const cols = Object.keys(missingData);
        const counts = Object.values(missingData);

        const data = [{
            x: cols,
            y: counts,
            type: 'bar',
            marker: {
                color: counts.map(c => c > 0 ? '#ef4444' : '#10b981'),
                borderRadius: 4
            }
        }];

        const layout = {
            title: { text: 'Missing Values Count per Column', font: { size: 14 } },
            xaxis: { title: 'Column Name', tickangle: -30 },
            yaxis: { title: 'Missing Rows' },
            margin: { t: 40, b: 80, l: 50, r: 20 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent"
        };

        Plotly.newPlot(elementId, data, layout, { responsive: true, displayModeBar: false });
    },

    renderOutlierBoxPlot(elementId, numericValues, colName) {
        const data = [{
            y: numericValues,
            type: 'box',
            name: colName,
            marker: { color: '#3b82f6' },
            boxpoints: 'outliers'
        }];

        const layout = {
            title: { text: `Outlier Detection Box Plot: ${colName}`, font: { size: 14 } },
            yaxis: { title: 'Value Range' },
            margin: { t: 40, b: 40, l: 50, r: 20 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent"
        };

        Plotly.newPlot(elementId, data, layout, { responsive: true, displayModeBar: false });
    },

    renderHistogram(elementId, rawVals, cleanVals, colName) {
        const data = [
            {
                x: rawVals,
                type: 'histogram',
                name: 'Raw Data',
                opacity: 0.6,
                marker: { color: '#ef4444' }
            }
        ];

        if (cleanVals && cleanVals.length) {
            data.push({
                x: cleanVals,
                type: 'histogram',
                name: 'Cleaned Data',
                opacity: 0.6,
                marker: { color: '#10b981' }
            });
        }

        const layout = {
            title: { text: `Distribution Comparison: ${colName}`, font: { size: 14 } },
            barmode: 'overlay',
            margin: { t: 40, b: 40, l: 50, r: 20 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent"
        };

        Plotly.newPlot(elementId, data, layout, { responsive: true });
    },

    renderCorrelationHeatmap(elementId, corrObj) {
        if (!corrObj || !corrObj.columns || corrObj.columns.length < 2) {
            document.getElementById(elementId).innerHTML = "<p class='text-muted' style='text-align:center; padding: 3rem;'>Correlation Heatmap requires at least 2 numerical columns.</p>";
            return;
        }

        const data = [{
            z: corrObj.matrix,
            x: corrObj.columns,
            y: corrObj.columns,
            type: 'heatmap',
            colorscale: 'Blues',
            zmin: -1,
            zmax: 1
        }];

        const layout = {
            title: { text: 'Numerical Correlation Heatmap', font: { size: 14 } },
            margin: { t: 40, b: 80, l: 100, r: 20 },
            paper_bgcolor: "transparent"
        };

        Plotly.newPlot(elementId, data, layout, { responsive: true });
    }
};
