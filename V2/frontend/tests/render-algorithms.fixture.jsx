import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {MemoryRouter} from 'react-router-dom';
import NLPPanel from '../src/components/NLPPanel';

export function render(analysis, records = []) {
  return renderToStaticMarkup(<MemoryRouter><NLPPanel analysis={analysis} records={records}/></MemoryRouter>);
}
