import React from "react";

export enum ExternalLinkType {
  truenasGUI = 80,
  portainer = 10201,
  homeassistant = 10101,
  nextcloud = 10302,
  plex = 32400,
}

function getExternalURL(link: ExternalLinkType) {
  const hostname = window.location.hostname;
  let scheme: String;
  switch (link) {
    case (ExternalLinkType.truenasGUI, ExternalLinkType.plex):
      scheme = "http";
      break;
    default:
      scheme = "https";
  }
  return `${scheme}://${hostname}:${link.valueOf()}`;
}

interface ExternalLinkData {
  target: ExternalLinkType;
  title: String;
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
        target="_blank"
        rel="noopener noreferrer"
      >
        {this.props.title}
      </a>
    );
  }
}
