**COVID-19 cases in the San Francisco Bay Area**

Updated daily from [public data](https://github.com/CSSEGISandData/COVID-19).

See the dashboard here: https://florinandrei.github.io/c19sfba/

A few words about the smoothing function:

The data is very noisy, there's a lot of up-and-down variation from day to day. For a single graph that's not a big deal, but with 9 graphs plotted at once, that makes it very hard to see anything.

Naive averages don't do much for smoothing, unless you use a very big interval. But then the data becomes too flattened. Instead, I use a Blackman-Harris window, which is essentially a bell curve - so values close to current are more important to the average, while values far away from current only matter a little.

It's kind of equivalent to a simple, short window (since only days close to current actually matter a lot) but looks better.

No data is lost, it's just smeared out a little. Since there is quite a bit of uncertainty in the data anyway, this doesn't matter much; moerover, the uncertainty itself is rather bell-shaped, so this is likely a good guess. A regular 7-day window also spreads out the data (it's inevitable with smoothing), but looks worse.

https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.blackmanharris.html#scipy.signal.windows.blackmanharris
