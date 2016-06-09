import ga from 'react-ga';

export function sendGoogleAnalyticsEvent(category, action, label, value) {
  let event = {
    category: category,
    action: action,
    label: label,
  };
  if (value !== undefined) {
    event.value = value;
  }
  ga.event(event);
}
