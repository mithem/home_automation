import React from "react"
import DockerVolumeData from "../models/DockerVolumeData"
import {Button} from "react-bootstrap"
import {removeVolume} from "../functions"

import "../style/ListItem.css"

export default class DockerVolume extends React.Component<{volume: DockerVolumeData}> {
	render() {
		return (
			<div className="docker-volume list-item">
				<span className="name">{this.props.volume.name}</span>
				<Button
					className="action"
					variant="danger"
					onClick={() => {removeVolume(this.props.volume.id)}}>
					Remove
				</Button>
			</div>
		)
	}
}
