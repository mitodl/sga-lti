import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import {
    UPDATE_CHECKBOX
} from '../actions';

// Helper function to avoid a commonly repeated pattern where we merge
// state with something computed solely from the actions. Accepts a
// function that will get the action, and should return the value to
// be merged with the existing state.
function payloadMerge(fn) {
  return (state, action) => {
    return Object.assign({}, state, fn(action));
  };
}

const INITIAL_CHECKBOX_STATE = {
  checked: false
};

export const checkbox = handleActions({
  UPDATE_CHECKBOX: payloadMerge((action) => ({
    checked: action.payload.checked,
  }))
}, INITIAL_CHECKBOX_STATE);

export default combineReducers({
  checkbox
});

