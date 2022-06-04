import React from "react";

export enum ExternalLinkType {
  truenasGUI = 443,
  portainer = 10201,
  homeassistant = 10101,
  nextcloud = 10302,
  plex = 32400,
  heimdall = 11401,
}

function getExternalURL(link: ExternalLinkType) {
  const hostname = window.location.hostname;
  let scheme: String;
  switch (link) {
    default:
      scheme = "https";
  }
  return `${scheme}://${hostname}:${link.valueOf()}`;
}

interface ExternalLinkData {
  target: ExternalLinkType;
  title: String;
  openInCurrentTab?: boolean;
}

export default class ExternalLink extends React.Component<
  ExternalLinkData,
  {}
> {
  public render() {
    return (
      <a
        href={getExternalURL(this.props.target)}
        className="nav-link"
        target={this.props.openInCurrentTab ? "_self" : "_blank"}
        rel="noopener noreferrer"
      >
        {this.props.title}
      </a>
    );
  }
}
