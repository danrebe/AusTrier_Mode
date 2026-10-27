//Funktions die ähliche bilder zum ausgewählten Bild zurückgibt
function imageChosen(bildIndex: number, filter: string): string[] {
    const bildArray = bilder[filter as keyof typeof bilder];

    if (!bildArray || bildIndex < 0 || bildIndex >= bildArray.length) {
        return [];
    }

    const start = Math.max(0, bildIndex - 3);
    const end = Math.min(bildArray.length, bildIndex + 4);

    return bildArray.slice(start, end);
}

