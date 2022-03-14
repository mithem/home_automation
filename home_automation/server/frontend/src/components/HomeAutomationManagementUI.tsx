import React from "react";
import { Alert, Button, Card } from "react-bootstrap";
import { refreshInterval } from "../constants";
import {
  getHomeAutomationManagementData,
  upgradeServer,
  refreshVersionInfo,
  upgradeHomeAssistant,
  compress,
  archive,
} from "../functions";
import HomeAutomationManagementData from "../models/HomeAutomationManagementData";

import "../style/HomeAutomationManagementUI.css";

export default class HomeAutomationManagementUI extends React.Component<
  {},
  HomeAutomationManagementData
> {
  timerID: any;
  constructor(props: any) {
    super(props);
    this.state = {
      version: undefined,
      available: undefined,
      versionAvailableFetchingError: undefined,
      homeAssistantUpdateError: undefined,
      upgradeServerError: undefined,
      newHomeAssistantVersion: undefined,
      otherError: undefined,
    };
    this.timerID = undefined;
  }

  async getData() {
    getHomeAutomationManagementData()
      .then((data) => {
        if (data.version === undefined) {
          this.setState({
            versionAvailableFetchingError: Error("No version data."),
          });
        }
        // a) undefine the error in one line
        // b) clear available version once it's no longer newer
        this.setState({
          version: data.version,
          available: data.available,
          versionAvailableFetchingError: undefined,
        });
      })
      .catch((error) => {
        this.setState({
          version: undefined,
          available: undefined,
          versionAvailableFetchingError: error as Error,
        });
      });
  }

  upgradeServer() {
    upgradeServer()
      .then((result) => {
        if (!result.success) {
          this.setState({ upgradeServerError: result.error });
        }
      })
      .catch((error) => {
        this.setState({ upgradeServerError: new Error(error.response.data) });
      });
  }

  upgradeHomeAssistant() {
    upgradeHomeAssistant()
      .then((result) => {
        if (!result.success) {
          this.setState({ homeAssistantUpdateError: result.error });
        } else {
          this.setState({
            homeAssistantUpdateError: undefined,
            newHomeAssistantVersion: result.newVersion,
          });
        }
      })
      .catch((error) => {
        this.setState({
          homeAssistantUpdateError: new Error(error.response.data.error),
        });
      });
  }

  compress() {
    compress().catch((error) => {
      this.setState({ otherError: new Error(error.response.data.error) });
    });
  }

  archive() {
    archive().catch((error) => {
      this.setState({ otherError: new Error(error.response.data.error) });
    });
  }

  render() {
    const newVersionAvailableAlert =
      this.state.available !== undefined ? (
        <Alert variant="success" className="version available">
          <span>
            A new version is available: {this.state.available.version} (checked{" "}
            {this.state.available.availableSince})!
          </span>
          <Button
            variant="primary"
            onClick={() => {
              this.upgradeServer();
            }}
          >
            Upgrade
          </Button>
        </Alert>
      ) : null;
    const newHomeAssistantVersionSuccessAlert =
      this.state.homeAssistantUpdateError === undefined &&
      this.state.newHomeAssistantVersion !== undefined ? (
        <Alert variant="success" className="">
          Successfully updated Home Assistant version to
          {this.state.newHomeAssistantVersion ?? "(N/A)"}!
        </Alert>
      ) : null;
    const errors = [];
    for (const error of [
      this.state.versionAvailableFetchingError,
      this.state.upgradeServerError,
      this.state.homeAssistantUpdateError,
      this.state.otherError,
    ]) {
      if (error !== undefined) {
        errors.push(<Alert variant="danger">{error.message}</Alert>);
      }
    }
    return (
      <div className="home-automation-management-gui item-list">
        {errors}
        {newHomeAssistantVersionSuccessAlert}
        <Alert variant="secondary" className="version current">
          <span>Current version: {this.state.version ?? "N/A"}</span>
          <Button variant="primary" onClick={() => refreshVersionInfo}>
            Check for updates
          </Button>
        </Alert>
        {newVersionAvailableAlert}
        <Card>
          <Card.Body>
            <Button variant="primary" onClick={() => this.upgradeHomeAssistant()}>
              Upgrade home assistant
            </Button>
            <Button variant="primary" onClick={() => this.compress()}>
              Compress
            </Button>
            <Button variant="primary" onClick={() => this.archive()}>
              Archive
            </Button>
          </Card.Body>
        </Card>
      </div>
    );
  }

  componentDidMount() {
    this.getData();
    this.timerID = setInterval(() => {
      this.getData();
    }, refreshInterval);
  }

  componentWillUnmount() {
    clearInterval(this.timerID);
  }
}
