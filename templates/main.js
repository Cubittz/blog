(function() {
    var editLinks = document.querySelectorAll('[id^="show-form-"]');
    var editComments = document.querySelectorAll('[id^="edit-comment-"]');
    var originalComments = document.querySelectorAll('[id^="original-comment-"]');
    var cancelComments = document.querySelectorAll('[id^="cancel-comment-"]');

    addEvents(editLinks, showForm);
    addEvents(cancelComments, closeForm);

    function addEvents(obj, func) {
        for (o of obj) {
            o.addEventListener("click", func);
        }
    };

    function showForm(e) {
        var id = e.target.id.split('-')[2];
        var editComment = editComments[id-1];
        editComment.style.display = 'block';
        var originalComment = originalComments[id-1];
        originalComment.style.display = 'none';
    };

    function closeForm(e) {
        var id = e.target.id.split('-')[2];
        var editComment = editComments[id-1];
        editComment.style.display = 'none';
        var originalComment = originalComments[id-1];
        originalComment.style.display = 'block';
    };

})();