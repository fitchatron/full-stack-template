import { createHmac, createHash } from "crypto";
import bcrypt from "bcrypt";

export function cryptoService() {
  function createPepperHash() {
    const hash = createHash("sha256");
    const hex = hash.digest("hex");
    return hex;
  }

  function hashStringWithPepper(data: string) {
    const pepper = process.env.PEPPER_HASH;
    if (!pepper)
      throw new Error(
        "PEPPER_HASH not defined. Add to env file before proceeding",
      );
    const hmac = createHmac("sha256", pepper);
    const hex = hmac.update(data).digest("hex");
    return hex;
  }

  async function generateSaltAndHash(
    value: string,
    options?: { hashWithpepper: boolean; rounds: number },
  ) {
    const _options = {
      hashWithpepper: options?.hashWithpepper ?? true,
      rounds: options?.rounds ?? 10,
    };
    const salt = await bcrypt.genSalt(_options.rounds);
    const data = _options.hashWithpepper ? hashStringWithPepper(value) : value;
    const hash = await bcrypt.hash(data, salt);
    return { hash, salt };
  }

  async function compareValueToHash(
    value: string,
    hash: string,
    options?: { hashWithpepper: boolean },
  ) {
    const _options = {
      hashWithpepper: options?.hashWithpepper ?? true,
    };

    const data = _options.hashWithpepper ? hashStringWithPepper(value) : value;

    return bcrypt.compare(data, hash);
  }
  return {
    createPepperHash,
    hashStringWithPepper,
    generateSaltAndHash,
    compareValueToHash,
  };
}
