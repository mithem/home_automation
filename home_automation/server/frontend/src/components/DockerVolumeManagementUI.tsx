import React from "react";
import DockerVolumeData from "../models/DockerVolumeData";
import DockerVolume from "./DockerVolume";
import { refreshInterval } from "../constants";
import { Alert, Spinner } from "react-bootstrap";

import "../style/DockerManagementUI.css";
import { getVolumes } from "../functions";

export default class DockerManagmentUI extends React.Component<
  {},
  { volumes: DockerVolumeData[]; error?: Error; loading: boolean }
> {
  timerID: any; // either, I declare this as `number` and componentDidMount can't assign value of type `Timeout` to timerID or I declare this as `Timeout`, which then can't be found in current context!?
  // my justification: https://spin.atomicobject.com/2018/11/08/countdown-timer-react-typescript/
  constructor(props: any) {
    super(props);
    this.state = { volumes: [], error: undefined, loading: false };
    this.timerID = -1;
  }

  getVolumes() {
    if (!this.state.loading) {
      getVolumes()
        .then((data) => {
          this.setState(data);
          this.setState({ error: undefined, loading: false });
        })
        .catch((error) => {
          this.setState({ error: error as Error, loading: false });
        });
    }
  }

  render() {
    const volumeList = this.state.volumes.map((volume) => {
      return <DockerVolume volume={volume} key={volume.id} />;
    });

    const apiError =
      this.state.error !== undefined ? (
        <Alert variant="danger">
          There was an error fetching docker volumes: {this.state.error.message}
        </Alert>
      ) : null;

    const loadingSpinner = this.state.loading ? (
      <Spinner animation="border" />
    ) : null;

    const noVolumesWarning =
      this.state.volumes.length === 0 ? (
        <Alert variant="info">
          You currently don't have any docker volumes. Create some (e.g. by
          creating a container with one) to view them here.
        </Alert>
      ) : null;

    return (
      <div className="item-list volume-list">
        {apiError}
        {noVolumesWarning}
        {loadingSpinner}
        {volumeList}
      </div>
    );
  }
  componentDidMount() {
    this.getVolumes();
    this.timerID = setInterval(() => {
      this.getVolumes();
    }, refreshInterval);
  }
  componentWillUnmount() {
    clearInterval(this.timerID);
  }
}
