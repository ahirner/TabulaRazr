Table = React.createClass({
  propTypes: {
    // This component gets the table to display through a React prop.
    // We can use propTypes to indicate it is required
    table: React.PropTypes.object.isRequired
  },

  render() {
    // Give tables a different className when they are checked off,
    // so that we can style them nicely in CSS
    const tableClassName = this.props.table.checked ? "checked" : "";
 
    return (
      <span>"hello"</span>
    );
  }
});