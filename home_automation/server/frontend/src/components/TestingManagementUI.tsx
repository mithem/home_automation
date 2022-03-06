import React from "react";
import { Alert, Button } from "react-bootstrap";
import {
  testingSetVersionAvailable,
  testingInitiateAutoUpgrade,
  forceHomeAssistantUpdate,
} from "../functions";
import TestingManagementData from "../models/TestingManagementData";

export default class TestingManagementUI extends React.Component<
  {},
  TestingManagementData
> {
  constructor(props: any) {
    super(props);
    this.state = { error: undefined };
  }

  setVersionAvailable() {
    testingSetVersionAvailable();
  }

  initiateAutoUpgrade() {
    testingInitiateAutoUpgrade();
  }

  forceHomeAssistantUpdate() {
    const newVersion = prompt("New version?");
    if (newVersion != null) {
      forceHomeAssistantUpdate(newVersion)
        .then((result) => {
          if (result.error !== null) {
            this.setState({ error: result.error });
          }
        })
        .catch((error) => {
          this.setState({ error: new Error(error.response.data.error) });
        });
    }
  }

  render() {
    const alert =
      this.state.error !== undefined ? (
        <Alert variant="danger">
          Error updating home assistant: {this.state.error.message}
        </Alert>
      ) : null;
    return (
      <div className="testing-management">
        {alert}
        <Button variant="primary" onClick={() => this.setVersionAvailable()}>
          Set version available
        </Button>
        <br />
        <br />
        <Button variant="primary" onClick={() => this.initiateAutoUpgrade()}>
          Initiate auto upgrade
        </Button>
        <br />
        <br />
        <Button
          variant="primary"
          onClick={() => this.forceHomeAssistantUpdate()}
        >
          Force home assistant update
        </Button>
      </div>
    );
  }
}
