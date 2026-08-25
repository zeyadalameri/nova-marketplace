type ProductVisualProps = {
  name: string;
  slug: string;
  image?: string;
};

function ProductIllustration({ slug }: { slug: string }) {
  if (slug === "wireless-headphones") {
    return <><path d="M82 130v-18c0-55 35-87 78-87s78 32 78 87v18"/><rect x="60" y="116" width="50" height="88" rx="23"/><rect x="210" y="116" width="50" height="88" rx="23"/><path d="M110 172c13 30 31 43 50 43s37-13 50-43"/></>;
  }
  if (slug === "mechanical-keyboard") {
    return <><rect x="36" y="66" width="248" height="132" rx="18"/><path d="M58 94h22m15 0h22m15 0h22m15 0h22m15 0h22m15 0h22M58 126h28m15 0h28m15 0h28m15 0h28m15 0h28M58 158h32m14 0h112m14 0h32"/><path d="M82 198l-12 18m168-18 12 18"/></>;
  }
  if (slug === "smart-watch") {
    return <><path d="M124 60l10-42h52l10 42M124 180l10 42h52l10-42"/><rect x="100" y="52" width="120" height="136" rx="32"/><circle cx="160" cy="120" r="38"/><path d="M160 96v26l18 12"/><path d="M220 102h10v30h-10"/></>;
  }
  if (slug === "smart-desk-lamp") {
    return <><path d="M90 204h140M160 198v-40m0 0l-42-30m42 30 38-74"/><circle cx="201" cy="76" r="15"/><path d="M196 62l28-28c17 17 22 37 14 59l-39-4"/><path d="M142 204c0-12 8-21 18-21s18 9 18 21"/></>;
  }
  if (slug === "cotton-shirt") {
    return <><path d="M116 43l-54 31 24 49 27-14v101h94V109l27 14 24-49-54-31c-9 15-24 23-44 23s-35-8-44-23z"/><path d="M134 52c5 18 13 27 26 27s21-9 26-27M113 109v-30m94 30V79"/></>;
  }
  return <><path d="M70 80h180l-10 132H80L70 80z"/><path d="M118 80V61c0-23 17-38 42-38s42 15 42 38v19"/><path d="M70 111h180M109 112v99m102-99v99"/><circle cx="160" cy="144" r="18"/><path d="M151 144h18"/></>;
}

const spriteMap: Record<string, { sheet: "a" | "b"; cell: number }> = {
  "wireless-headphones": { sheet: "a", cell: 1 },
  "wireless-earbuds": { sheet: "a", cell: 1 },
  "compact-laptop": { sheet: "a", cell: 2 },
  "nova-tablet": { sheet: "a", cell: 2 },
  "smart-desk-lamp": { sheet: "a", cell: 3 },
  "ambient-table-lamp": { sheet: "a", cell: 3 },
  "running-shoes": { sheet: "a", cell: 4 },
  "training-shoes": { sheet: "a", cell: 4 },
  "espresso-machine": { sheet: "a", cell: 5 },
  "travel-suitcase": { sheet: "a", cell: 6 },
  "nova-phone-x": { sheet: "b", cell: 1 },
  "smart-watch": { sheet: "b", cell: 2 },
  "mechanical-keyboard": { sheet: "b", cell: 3 },
  "compact-keyboard": { sheet: "b", cell: 3 },
  "air-fryer": { sheet: "b", cell: 4 },
  "cotton-shirt": { sheet: "b", cell: 5 },
  "city-backpack": { sheet: "b", cell: 6 },
  "travel-backpack": { sheet: "b", cell: 6 },
};

export function ProductVisual({ name, slug, image }: ProductVisualProps) {
  if (image) {
    return <span className="product-art product-art-photo" role="img" aria-label={name} style={{ backgroundImage: `url(${image})` }} />;
  }

  const sprite = spriteMap[slug];
  if (sprite) {
    return (
      <span
        className={`product-art product-art-sprite sprite-${sprite.sheet} sprite-cell-${sprite.cell}`}
        role="img"
        aria-label={`صورة ${name}`}
      />
    );
  }

  return (
    <span className={`product-art art-${slug}`} role="img" aria-label={`صورة توضيحية لـ ${name}`}>
      <span className="art-glow" />
      <svg viewBox="0 0 320 240" aria-hidden="true">
        <ProductIllustration slug={slug} />
      </svg>
    </span>
  );
}
