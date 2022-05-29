import React from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";

import DockerContainerManagementUI from "./components/DockerContainerManagementUI";
import DockerVolumeManagementUI from "./components/DockerVolumeManagementUI";
import HomeAutomationManagementUI from "./components/HomeAutomationManagementUI";
import ConfigManagementUI from "./components/ConfigManagementUI";
import Navbar from "./components/Navbar";
import ErrorNotFound from "./components/ErrorNotFound";

import "./style/App.css";

export default class App extends React.Component {
  render() {
    const swi = (
      <Switch>
        <Route exact path="/">
          <HomeAutomationManagementUI />
        </Route>
        <Route exact path="/docker/containers">
          <DockerContainerManagementUI />
        </Route>
        <Route exact path="/docker/volumes">
          <DockerVolumeManagementUI />
        </Route>
        <Route exact path="/config">
          <ConfigManagementUI />
        </Route>
        <Route path="/">
          <ErrorNotFound />
        </Route>
      </Switch>
    );
    return (
      <Router>
        <Navbar />
        <div className="content">{swi}</div>
      </Router>
    );
  }
}
