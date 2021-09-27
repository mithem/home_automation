import React from "react"
import DockerContainerData from "../models/DockerContainerData"
import { removeContainer, startContainer, stopContainer } from "../functions"
import {Button} from "react-bootstrap"

import "../style/ListItem.css"
import "bootstrap/dist/css/bootstrap.min.css"

export default class DockerContainer extends React.Component<{container: DockerContainerData, key: string}> {
	render() {
		const stopBtn = this.props.container.state === "running" ? (
		  <Button
			variant="danger"
			onClick={() => {
				stopContainer(this.props.container.name)
			}}
		  >
		    Stop
		  </Button>) : null
		const startAndDeleteBtns = this.props.container.state === "exited" ? (
		  <div>
		    <Button
		      variant="primary"
		      onClick={() => {
			startContainer(this.props.container.name)
		      }}
		    >
		      Start
		    </Button>
		    <Button
		      variant="danger"
		      onClick={() => {
			removeContainer(this.props.container.name)
		      }}
		    >
		      Delete
		    </Button>
		  </div>
		  ) : null
		return (
		<div className="docker-container list-item">
			<span className="name">{this.props.container.name}</span>
			<span className={`status ${this.props.container.state}`}>{this.props.container.state}</span>
			<span className="tags">{this.props.container.image.tags.join(", ")}</span>
			{stopBtn}
			{startAndDeleteBtns}
		</div>
		);
	}
}
