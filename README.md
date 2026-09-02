## Fama-French Three-Factor Model: Replication and Post-2000 Extension
  This project replicates the empirical methodology of Fama and French (1993), "Common Risk Factors in the Returns on Stocks and Bonds." The script pulls monthly stock data from a 100-year time frame (1926-2026) provided through Ken French's Data Library. The data includes the three factors used in the model: the market risk premium (Mkt-RF), the size factor (SMB, small minus big), and the value factor (HML, high minus low book-to-market), along with a 5x5 sort of portfolios classified by size and book-to-market.

  Each portfolio uses an OLS regression to estimate the fraction of total excess return (return above RF, the risk-free rate) which can be attributed to the three factors. Together, the regressions test whether market risk, size, and value collectively explain differences in stock returns across a variety of small/large and value/growth stocks.

  Beyond a mere replication, this project extends to include a post-2000 split-sample analysis, testing whether the explanatory power, as well as the size and value risk premia, have meaningfully changed in the decades following the original study's publication.

## Model

For each portfolio $i$:

$$R_{i,t} - RF_t = \alpha_i + \beta_{mkt}(Mkt\text{-}RF)_t + \beta_{smb}\,SMB_t + \beta_{hml}\,HML_t + \epsilon_t$$

estimated separately via OLS across all 25 portfolios.

- **$R_{i,t} - RF_t$**: portfolio $i$'s excess return in month $t$ (return above the risk-free rate).
- **$\alpha_i$**: the average monthly excess return left unexplained by the three factors. A value near zero and statistically insignificant means the model fully accounts for that portfolio's return.
- **$\beta_{mkt}, \beta_{smb}, \beta_{hml}$**: how sensitive the portfolio's return is to movement in each factor, estimated as the best-fit slope across all 1200 months.
- **$Mkt\text{-}RF$, $SMB$, $HML$**: the three factors themselves (market, size, and value risk premia).
- **$\epsilon_t$**: the error term, month-to-month noise not captured by alpha or the three factors.

$RF$ is subtracted from portfolio returns before regressing because it does not vary across portfolios in a given month and is not compensation for risk. If it remained in the regression, $\alpha$ would change through shifting baseline values unrelated to risk.
## Data
Data pulled from [Ken French's Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), monthly, July 1926 to June 2026 (1200 months): F-F Research Data Factors (Mkt-RF, SMB, HML, RF) and 25 Portfolios Formed on Size and Book-to-Market (5x5), value-weighted.
## Results

**Full sample:**

Across the 25 portfolios, the three-factor model generally fits well. Most portfolio $R^2$ values sit between 0.85 and 0.95, with $\alpha$ values not statistically distinguishable from zero. One outlier is SMALL LoBM, with a notably lower $R^2$ (0.66) and a negative alpha (-0.67%/month, p = 0.00088). 6 of 25 portfolios show a statistically significant alpha, compared to an expected 1.25 at the 5% significance level. This result is consistent with idiosyncratic, firm-specific risk that broad factors do not capture, especially among the aforementioned SMALL LoBM portfolio, containing small-cap growth stocks.

**Post-2000 Extension:**

The SMB and HML premia appeared lower after 2000 (SMB: 2.22% to 1.41% annualised; HML: 4.81% to 2.71%). Both declines, however, fell well short of statistical significance (p = 0.74 and 0.44 respectively).

| Factor | Annualized mean, pre-2000 | Annualized mean, post-2000 | p-value |
|---|---|---|---|
| SMB | 2.22% | 1.41% | 0.74 |
| HML | 4.81% | 2.71% | 0.44 |

Model fit remained stable, with only small movements in $R^2$ and $\alpha$ that were not tested for significance.

| | Pre-2000 | Post-2000 |
|---|---|---|
| Average absolute alpha | 0.127%/mo | 0.139%/mo |
| Share of significant alphas | 16% (4/25) | 20% (5/25) |
| Average R² | 0.912 | 0.898 |

Though these numbers are consistent with ideas of factor decay in the decades following publication (McLean and Pontiff, 2016), this analysis does not provide any reliable evidence that the size and value premia have weakened.

## Limitations 
- Instead of rebuilding factors from raw CRSP/Compustat data, portfolios are inherited from Ken French's library, and therefore inherit any conventions or revisions to the data
- The post-2000 model fit comparison was not tested for statistical significance and is descriptive only. A formal test, such as a Chow test, would be needed to assess whether the regression relationship genuinely differs between periods.
- Splitting the sample decreases available observations for each sub-period regression.
- $R^2$ can shift between periods due to changes in overall market volatility (dot-com crash, 2008, COVID) rather than changes in the underlying factor relationship. Though not directly tested, small deviations in $R^2$ and $\alpha$ would appear consistent with volatility-driven impacts.
  
## Usage
- Install dependencies: `pip install -r requirements.txt`
- Run the script: `python3 fama_french_replication.py`
- Running it creates an `output/` folder with the result CSVs
## References

Fama, E. F., & French, K. R. (1993). Common Risk Factors in the Returns on Stocks and Bonds. *Journal of Financial Economics*, 33(1), 3-56.

McLean, R. D., & Pontiff, J. (2016). Does Academic Research Destroy Stock Return Predictability? *The Journal of Finance*, 71(1), 5-32.
