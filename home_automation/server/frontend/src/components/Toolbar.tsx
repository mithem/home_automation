import React from "react";
import {Button, ButtonGroup, ButtonToolbar} from "react-bootstrap";
import {composePull, composeUp, composeDown, dockerStatus, dockerPrune} from "../functions";
import DockerComposeStatusDescription from "./DockerComposeStatusDescription";
import { refreshInterval } from "../constants";

export default class Toolbar extends React.Component<{}, {pulling: boolean, upping: boolean, downing: boolean, loading: boolean, pruning: boolean}> {
	timerID: any
	constructor(props: any) {
		super(props)
		this.state = {pulling: false, upping: false, downing: false, pruning: false, loading: false}
		this.timerID = -1
	}
	async getDockerStatus() {
		if (!this.state.loading) {
			this.setState({loading: true})
			dockerStatus()
				.then(state => {
					this.setState(state)
					this.setState({loading: false})
				})
				.catch((_) => {})
		}
	}
	runCatchingExceptions(f: CallableFunction) {
		f()
			.catch((_: any) => {})
	}
	render() {
		return (
			<div className="toolbar">
				<ButtonToolbar>
					<DockerComposeStatusDescription pulling={this.state.pulling} upping={this.state.upping} downing={this.state.downing} pruning={this.state.pruning} />
					<ButtonGroup>
						<Button variant="primary" disabled={this.buttonsDisabled()} onClick={() => this.runCatchingExceptions(composePull)}>Compose pull</Button>
						<Button variant="primary" disabled={this.buttonsDisabled()} onClick={() => this.runCatchingExceptions(composeUp)}>Compose up</Button>
						<Button variant="danger" disabled={this.buttonsDisabled()} onClick={() => this.runCatchingExceptions(composeDown)}>Compose down</Button>
						<Button variant="danger" disabled={this.buttonsDisabled()} onClick={() => this.runCatchingExceptions(dockerPrune)}>Docker prune</Button>
					</ButtonGroup>
				</ButtonToolbar>
			</div>
		)
	}
	componentDidMount() {
		this.getDockerStatus()
		this.timerID = setInterval(() => {
			this.getDockerStatus()
		}, refreshInterval)
	}
	componentWillUnmount() {
		clearInterval(this.timerID)
	}
	buttonsDisabled() {
		return ((this.state.pulling || this.state.upping) || this.state.downing) || this.state.pruning
	}
}
