$(document).ready(function(){
    $('.auto-submit-star').rating({
	callback:function(value, link){
	    $(this.form).ajaxSubmit();
	},
	cancelValue:'test'
    });
});
