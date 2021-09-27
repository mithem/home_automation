import React from "react"

export default class ErrorNotFound extends React.Component<{path: string}> {
	render() {
		return (
			<div className="card">
				<h1>404 - Not found.</h1>
				<p>The page you requested ({this.props.path}) is not found.</p>
			</div>
		)
	}
}
