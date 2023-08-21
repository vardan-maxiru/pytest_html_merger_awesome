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
        const resulttable = find('#results-table');
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

function filterTable(elem) { // eslint-disable-line no-unused-vars
    const outcomeAtt = 'data-test-result';
    const outcome = elem.getAttribute(outcomeAtt);
    const outcomeRows = document.querySelectorAll('.' + outcome);

    for(let i = 0; i < outcomeRows.length; i++){
        elem.checked ? outcomeRows[i].classList.remove('hidden') : outcomeRows[i].classList.add('hidden');
    }
}

function getQueryParameter(name) {
    const match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
}

function find(selector, elem) { // eslint-disable-line no-redeclare
    if (!elem) {
        elem = document;
    }
    return elem.querySelector(selector);
}

function findAll(selector, elem) {
    if (!elem) {
        elem = document;
    }
    return toArray(elem.querySelectorAll(selector));
}

function init() {
    console.log("Initialize")
}