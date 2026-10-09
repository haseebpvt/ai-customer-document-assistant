export const STATUS_LABELS = {
  queued: 'Queued',
  identify_file_node: 'Checking file type',
  image_processing_node: 'Reading image',
  document_processing_node: 'Reading document',
  identify_document_node: 'Classifying',
  extract_fields_node: 'Extracting fields',
  missing_fields_node: 'Checking for missing fields',
  summary_node: 'Writing report',
  retrying: 'Retrying',
  completed: 'Completed',
  failed: 'Failed',
}

export function statusLabel(status) {
  return STATUS_LABELS[status] ?? status
}
