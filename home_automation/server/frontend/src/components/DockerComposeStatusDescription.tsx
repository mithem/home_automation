import React from "react";

import "../style/DockerComposeStatusDescription.css"

export default class DockerComposeStatusDescription extends React.Component<{pulling: boolean, upping: boolean, downing: boolean, pruning: boolean}, {}> {
	render() {
		if (this.props.pulling || this.props.upping || this.props.downing || this.props.pruning) {
			return(
				<span className="compose-status-description">
					{this.statusDescription()}
				</span>
			)
		} else {
			return null // to not mess up the layout (margin/gap of .compose-status-description)
		}
	}
	statusDescription() {
		// only one action can be active at any point anyways
		if (this.props.downing) {
			return "Downing..."
		} else if (this.props.upping) {
			return "Upping..."
		} else if (this.props.pulling) {
			return "Pulling..."
		} else if (this.props.pruning) {
			return "Pruning..."
		}
		return null
	}
}
