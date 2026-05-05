$(function () {
    $('#toggle-btn').click(navbarChange);
});

function navbarChange() {
    if ($('.home-page').hasClass('no-sidebar')) {
        $('.home-page').removeClass('no-sidebar');
        $('#side-bar').removeClass('sidebar-hide');
    } else {
        $('.home-page').addClass('no-sidebar');
        $('#side-bar').addClass('sidebar-hide');
    }
}