// Table component - represents a single todo item
Table = React.createClass({
  propTypes: {
    // This component gets the table to display through a React prop.
    // We can use propTypes to indicate it is required
    table: React.PropTypes.object.isRequired
  },

  toggleChecked() {
    // Set the checked property to the opposite of its current value
    Tables.update(this.props.table._id, {
      $set: {checked: ! this.props.table.checked}
    });
  },
 
  deleteThisTable() {
    Tables.remove(this.props.table._id);
  },

  render() {
    // Give tables a different className when they are checked off,
    // so that we can style them nicely in CSS
    const tableClassName = this.props.table.checked ? "checked" : "";
 
    return (
      

      <li className={tableClassName}>
        <button className="delete" onClick={this.deleteThisTable}>
          &times;
        </button>
 
        <input
          type="checkbox"
          readOnly={true}
          checked={this.props.table.checked}
          onClick={this.toggleChecked} />
 
        <span className="text">{this.props.table.text}</span>
      </li>
    );
  }
});