import solara

@solara.component
def Page():
	solara.Markdown(
		"""
		# Impact Page

		This is a simple Solara page with Markdown content.

		- Example item 1
		- Example item 2
		- Example item 3
		"""
	)
