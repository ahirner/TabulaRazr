// Table component - represents a single todo item
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
      <li className={tableClassName}>
        <a onClick={this.props.handleClick} className="text">{this.props.table._id.filename} - {this.props.table._id.project} - {this.props.table._id.table_id}</a>
      </li>
    );
  }
});