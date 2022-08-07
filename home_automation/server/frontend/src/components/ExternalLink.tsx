import React from "react";

interface ExternalLinkData {
  target: string;
  title: string;
  openInCurrentTab?: boolean;
}

export default class ExternalLink extends React.Component<
  ExternalLinkData,
  {}
> {
  public render() {
    return (
      <a
        href={this.props.target}
        className="nav-link"
        target={this.props.openInCurrentTab ? "_self" : "_blank"}
        rel="noopener noreferrer"
      >
        {this.props.title}
      </a>
    );
  }
}
