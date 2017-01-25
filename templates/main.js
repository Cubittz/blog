(function() {
    var editLinks = document.querySelectorAll('[id^="show-form-"]');
    var forms = document.querySelectorAll('[id^="edit-comment-"]');

    addEvents(editLinks, showForm);

    function addEvents(obj, func) {
        for (o of obj) {
            o.addEventListener("click", func);
        }
    }

    function showForm(e) {
        var id = e.target.id.split('-')[2];
        var form = forms[id-1];
        form.style.display = 'block';
    };
})();