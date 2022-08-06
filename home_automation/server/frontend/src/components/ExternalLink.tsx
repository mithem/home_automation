import React from "react";

interface ExternalLinkData {
  target: String;
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
        href={"https://" + this.props.target}
        className="nav-link"
        target={this.props.openInCurrentTab ? "_self" : "_blank"}
        rel="noopener noreferrer"
      >
        {this.props.title}
      </a>
    );
  }
}
