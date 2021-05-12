class GoalQuery {
    constructor(interactionOptions) {
        // required
        this.player = interactionOptions[0].value;
        this.opponent = interactionOptions[1].value;

        // optional
        this.season = interactionOptions.find((o) => o.name === 'season')?.value;
        this.competition = interactionOptions.find((o) => o.name === 'competition')?.value;
    }

}

GoalQuery.prototype.toString = function() {
    return [this.player, this.opponent, this.season, this.competition].join('\n');
}