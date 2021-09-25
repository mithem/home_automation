import React from "react";
import {Button, ButtonGroup, ButtonToolbar} from "react-bootstrap";
import {composePull, composeUp, composeDown, dockerStatus, dockerPrune} from "../functions";
import DockerComposeStatusDescription from "./DockerComposeStatusDescription";

export default class Toolbar extends React.Component<{}, {pulling: boolean, upping: boolean, downing: boolean, loading: boolean, pruning: boolean}> {
	timerID: any
	constructor(props: any) {
		super(props)
		this.state = {pulling: false, upping: false, downing: false, pruning: false, loading: false}
		this.timerID = -1
	}
	async getDockerStatus() {
		this.setState({loading: true})
		dockerStatus().then(state => {
			this.setState(state)
		})
	}
	render() {
		return (
			<div className="toolbar">
				<ButtonToolbar>
					<DockerComposeStatusDescription pulling={this.state.pulling} upping={this.state.upping} downing={this.state.downing} pruning={this.state.pruning} />
					<ButtonGroup>
						<Button variant="primary" disabled={this.buttonsDisabled()} onClick={() => composePull()}>Compose pull</Button>
						<Button variant="primary" disabled={this.buttonsDisabled()} onClick={() => composeUp()}>Compose up</Button>
						<Button variant="danger" disabled={this.buttonsDisabled()} onClick={() => composeDown()}>Compose down</Button>
						<Button variant="danger" disabled={this.buttonsDisabled()} onClick={() => dockerPrune()}>Docker prune</Button>
					</ButtonGroup>
				</ButtonToolbar>
			</div>
		)
	}
	componentDidMount() {
		this.getDockerStatus()
		this.timerID = setInterval(() => {
			this.getDockerStatus()
		}, 1000)
	}
	componentWillUnmount() {
		clearInterval(this.timerID)
	}
	buttonsDisabled() {
		return ( ( this.state.pulling || this.state.upping ) || this.state.downing ) || this.state.pruning
	}
}
