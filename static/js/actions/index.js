import { sendGoogleAnalyticsEvent } from '../util/util';
import { createAction } from 'redux-actions';

export const UPDATE_CHECKBOX = 'UPDATE_CHECKBOX';

export const updateCheckbox = createAction(
    UPDATE_CHECKBOX, checked =>  ({ checked }));
