function (doc, req) {
  return (req.query.variables.indexOf(doc.variable) != -1);
}
