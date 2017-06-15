function (doc) {
  emit([doc.environment, doc.timestamp], doc);
}
