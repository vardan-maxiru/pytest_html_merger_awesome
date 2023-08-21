document.addEventListener("DOMContentLoaded", () => {
    const cases = document.querySelectorAll(".case-row-headers");

    cases.forEach((case_item) => {
        case_item.onclick = function (event){
            const result = case_item.nextElementSibling
            if (result.classList.contains('open')) {
                result.classList.remove('open')
            } else {
                result.classList.add('open')
            }
        }
    })

    function addCollapse() {
        // Add links for show/hide all
        const resulttable = find('table.results-table');
        const showhideall = document.createElement('p');
        showhideall.innerHTML = '<a href="javascript:showAllExtras()">Show all details</a> / ' +
                                '<a href="javascript:hideAllExtras()">Hide all details</a>';
        resulttable.parentElement.insertBefore(showhideall, resulttable);
    
        // Add show/hide link to each result
        findAll('.col-result').forEach(function(elem) {
            const collapsed = getQueryParameter('collapsed') || 'Passed';
            const extras = elem.parentNode.nextElementSibling;
            const expandcollapse = document.createElement('span');
            if (extras.classList.contains('collapsed')) {
                expandcollapse.classList.add('expander');
            } else if (collapsed.includes(elem.innerHTML)) {
                extras.classList.add('collapsed');
                expandcollapse.classList.add('expander');
            } else {
                expandcollapse.classList.add('collapser');
            }
            elem.appendChild(expandcollapse);
    
            elem.addEventListener('click', function(event) {
                if (event.currentTarget.parentNode.nextElementSibling.classList.contains('collapsed')) {
                    showExtras(event.currentTarget);
                } else {
                    hideExtras(event.currentTarget);
                }
            });
        });
    }

    addCollapse()
});