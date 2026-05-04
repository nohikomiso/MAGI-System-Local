import React from 'react';
const $ = React.createElement;

export default function Modal({ setProps, name, is_open, question, answer }) {
    if (!is_open) return null;

    // データが不完全な場合のガード
    const safeQuestion = question || { id: 0, query: '' };
    const safeAnswer = answer || { id: 0, status: 'info', error: '', conditions: '', response: '' };

    const questionId = safeQuestion.id || 0;
    const answerId = safeAnswer.id || 0;

    let finalAnswer = safeAnswer;
    if (questionId !== answerId) {
        finalAnswer = { 
            id: questionId, 
            status: 'info', 
            error: '同期中...', 
            conditions: 'N/A', 
            response: 'データを取得しています。' 
        };
    }

    const close = () => {
        setProps({ is_open: false });
    };

    return $('div', { className: 'modal' },
        $('div', { className: 'modal-header' },
            $('div', { className: 'modal-title' }, name.toUpperCase()),
            $('div', { className: 'close', onClick: close }, 'X'),
        ),
        $('div', { className: 'modal-body' },
            $('div', { style: { fontWeight: 'bold' } }, 'QUESTION: '),
            $('div', { style: { marginBottom: '10px' } }, safeQuestion.query || '(無題)'),
            
            $('div', { style: { fontWeight: 'bold' } }, 'STATUS: '),
            $('div', { style: { marginBottom: '10px' } }, finalAnswer.status),
            
            $('div', { style: { fontWeight: 'bold' } }, 'ERROR: '),
            $('div', { style: { marginBottom: '10px' } }, finalAnswer.error || 'NONE'),
            
            $('div', { style: { fontWeight: 'bold' } }, 'CONDITIONS: '),
            $('div', { style: { marginBottom: '10px' } }, finalAnswer.conditions || 'NONE'),
            
            $('div', { style: { fontWeight: 'bold' } }, 'FULL RESPONSE: '),
            $('div', { style: { whiteSpace: 'pre-wrap' } }, finalAnswer.response || 'No data.')
        ),
    );
}

Modal.defaultProps = {
    is_open: false,
    question: { id: 0, query: '' },
    answer: { id: 0, status: 'info', error: '', conditions: '', response: '' }
};