import solara


@solara.component
def Page():
	solara.Markdown(
		"""
		# Mekong Delta Salinity & Subsidence Scenarios Dashboard

		Welcome to the dashboard exploring future salinity intrusion and land subsidence in the Mekong Delta. The underlying data and scenarios are based on the study:

		**"Future salinity intrusion and subsidence in the Mekong Delta: Impacts of climate change and human interventions"** ([Nature Communications Earth & Environment, 2021](https://www.nature.com/articles/s43247-021-00208-5)).

		This research combines climate projections, groundwater extraction, and riverbed erosion scenarios to assess risks to agriculture, water supply, and local communities. The dashboard allows you to interactively explore these scenarios and their impacts.
        
		## About the Data & Scenarios
		- **Climate Change:** RCP 4.5 and RCP 8.5 scenarios for 2030, 2040, and 2050.
		- **Subsidence:** Groundwater extraction-driven land subsidence.
		- **Riverbed Erosion:** Human-induced changes to river morphology.
		- **Combined Effects:** Explore how these drivers interact to affect salinity intrusion.
		"""
	)
	solara.Markdown(
		"""
		## Dashboard Pages
		- **Hazard:** View and compare salinity intrusion maps for different scenario combinations. Adjust climate, subsidence, and riverbed settings to see their effects on the delta.
		- **Impact:** Assess the consequences for agriculture, water resources, and population. This page provides summary statistics and visualizations of affected areas.

		---
		For more details, see the [Nature paper](https://www.nature.com/articles/s43247-021-00208-5).
		"""
	)
