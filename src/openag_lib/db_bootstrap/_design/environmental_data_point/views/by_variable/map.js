function (doc) {
  var point_type;
  if (doc.is_desired) {
    point_type = 'desired';
  }
  else {
    point_type = 'measured';
  }
  emit([doc.environment, point_type, doc.variable, doc.timestamp], doc);
}
