import React from "react";

export default class CheckboxWithLabel extends React.Component<{labelOn: string, labelOff: string}, {isChecked: boolean}> {
  constructor(props: {labelOn: string, labelOff: string}) {
	super(props)
  	this.state = {isChecked: false}
  }

  onChange () {
    	this.setState({isChecked: !this.state.isChecked})
  }

  render() {
	  return (
	    <label>
	      <input type="checkbox" checked={this.state.isChecked} onChange={this.onChange} />
	      {this.state.isChecked ? this.props.labelOn : this.props.labelOff}
	    </label>
	  )
  }
}
