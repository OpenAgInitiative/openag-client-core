function(newDoc, oldDoc, userCtx, secObj) {
  if (newDoc._deleted) {
    return;
  }
  var required_fields = ['environment', 'variable', 'is_desired', 'value', 'timestamp'];
  var field;
  for (var i in required_fields) {
    field = required_fields[i];
    if (!newDoc.hasOwnProperty(field)) {
      throw({forbidden: "EnvironmentalDataPoint instances are required to have a " + field + " field"});
    }
  }
}
